from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *

#====================|CBV====================
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import DeleteView
#====================CBV|====================

from django.http import HttpResponseForbidden

# Create your views here.

def homeView(request):
    return render(request, 'base.html')

@login_required(login_url='/login')
def perfilView(request):
    primerForm = PerfilForm(instance=request.user.perfilusuario)
    contexto = {'perfilUsuario': request.user.perfilusuario, 'form': primerForm}
    return render(request, 'perfil.html', contexto)

@login_required(login_url='/login')
def perfilEditarView(request):
    if request.method == 'POST':
        # Obtengo el formulario que recibe el servidor
        inputForm = PerfilForm(request.POST)
        if inputForm.is_valid():
            request.user.perfilusuario.nombresPila  = inputForm.cleaned_data.get('nombresPila')
            request.user.perfilusuario.apellido     = inputForm.cleaned_data.get('apellido')
            request.user.perfilusuario.direccion    = inputForm.cleaned_data.get('direccion')
            request.user.perfilusuario.telefono     = inputForm.cleaned_data.get('telefono')
            
            request.user.perfilusuario.save()

            print(inputForm.cleaned_data.get('nombresPila'))
            print(inputForm.cleaned_data.get('apellido'))
            print(inputForm.cleaned_data.get('direccion'))
            print(inputForm.cleaned_data.get('telefono'))

            replyForm = PerfilForm(instance=request.user.perfilusuario)
            contexto = {'perfilUsuario': request.user.perfilusuario, 'form': replyForm}
            return redirect(reverse_lazy('perfil'))
        else:
            print('Errors:', inputForm.errors)
    else:
        primerForm = PerfilForm(instance=request.user.perfilusuario)
        contexto = {'perfilUsuario': request.user.perfilusuario, 'form': primerForm}

        return render(request, 'perfil_editar.html', contexto)


def cuentasView(request):
    return render(request, 'cuentas.html')

#====================|Egreso====================#
class EgresoCBV:
    class EgresoCrear(LoginRequiredMixin, CreateView):
        model = Egreso
        form_class = EgresoForm
        template_name = 'finanzas_app/class_based_views/egresos/egreso_crear.html'
        success_url = reverse_lazy('egresos')

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            
            # 'instance' es el objeto que se está creando y que se pasará para
            # crear el formulario. Si le agrego la información de usuario, puedo
            # filtrar qué cuentas aparecen disponibles en la lista del formulario
            # llamando a egresoForm.__init__()
            if not kwargs.get('instance', None) or not kwargs['instance'].instance:
                kwargs['instance'] = Egreso(usuario=self.request.user.perfilusuario)
            return kwargs
        
        def form_valid(self, form):
            '''
            No pido información de a qué usuario pertenece
            porque corresponde al usuario actual.
            Se agrega esta información automáticamente una 
            vez se tiene el formulario válido 
            '''
            form.instance.usuario = self.request.user.perfilusuario

            # Actualizo las reservas de la cuenta
            cuenta = None
            if form.instance.formaDePago.cuenta:
                cuenta = form.instance.formaDePago.cuenta

            respuesta = super().form_valid(form)
            CuentaCBV.actualizarReservasCuenta(cuenta)
            return respuesta
        
    class EgresoDelete(LoginRequiredMixin, DeleteView):
        model = Egreso
        template_name = 'finanzas_app/class_based_views/egresos/egreso_eliminar.html'
        success_url = reverse_lazy('egresos')

        def form_valid(self, form):
            # Obtengo la cuenta del egreso a borrar...
            cuenta = None
            if form.instance.formaDePago.cuenta:
                cuenta = form.instance.formaDePago.cuenta
            # ...continuo con la ejecución normal (borra el egreso)...
            respuesta = super().form_valid(form)
            #...Recalcula el total
            CuentaCBV.actualizarReservasCuenta(cuenta)
            return respuesta

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda borrar los datos de otros usuarios
            '''
            egreso = self.get_object()
            if egreso.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede borrar este egreso.")
            
            return super().dispatch(request, *args, **kwargs)

    class EgresoUpdate(LoginRequiredMixin, UpdateView):
        model = Egreso
        form_class = EgresoForm
        template_name = 'finanzas_app/class_based_views/egresos/egreso_editar.html'
        success_url = reverse_lazy('egresos')

        def form_valid(self, form):
            # Obtengo la cuenta del egreso a borrar...
            cuenta = None
            if form.instance.formaDePago.cuenta:
                cuenta = form.instance.formaDePago.cuenta
            # ...continuo con la ejecución normal (edita el egreso)...
            respuesta = super().form_valid(form)
            #...Recalcula el total
            CuentaCBV.actualizarReservasCuenta(cuenta)
            return respuesta
        
        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda modificar la información de otros usuarios
            '''
            egreso = self.get_object()
            if egreso.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede editar este egreso.")

            return super().dispatch(request, *args, **kwargs)

    class EgresoList(LoginRequiredMixin, ListView):
        template_name = 'finanzas_app/class_based_views/egresos/egresos.html'
        model = Egreso

        def get_queryset(self):
            '''
            Sólo devuelve lo correspondiente al usuario actual
            '''
            return Egreso.objects.filter(usuario=self.request.user.perfilusuario)
#====================Egreso|====================#

#====================|Ingreso====================#
# Creo la clase IngresoCBV sólo por comodidad para programar
class IngresoCBV:
    class IngresoCrear(LoginRequiredMixin, CreateView):
        model = Ingreso
        form_class = IngresoForm
        template_name = 'finanzas_app/class_based_views/ingresos/ingreso_crear.html'
        success_url = reverse_lazy('ingresos')

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            
            # 'instance' es el objeto que se está creando y que se pasará para
            # crear el formulario. Si le agrego la información de usuario, puedo
            # filtrar qué cuentas aparecen disponibles en la lista del formulario
            # llamando a IngresoForm.__init__()
            if not kwargs.get('instance', None) or not kwargs['instance'].instance:
                kwargs['instance'] = Ingreso(usuario=self.request.user.perfilusuario)
            return kwargs
        
        def form_valid(self, form):
            '''
            No pido información de a qué usuario pertenece
            porque corresponde al usuario actual.
            Se agrega esta información automáticamente una 
            vez se tiene el formulario válido 
            '''
            form.instance.usuario = self.request.user.perfilusuario

            # Actualizo las reservas de la cuenta 
            form.instance.cuenta.reservas += form.instance.monto
            form.instance.cuenta.save()

            respuesta = super().form_valid(form)
            CuentaCBV.actualizarReservasCuenta(form.instance.cuenta)
            return respuesta
        
    class IngresoDelete(LoginRequiredMixin, DeleteView):
        model = Ingreso
        template_name = 'finanzas_app/class_based_views/ingresos/ingreso_eliminar.html'
        success_url = reverse_lazy('ingresos')

        def form_valid(self, form):
            # Obtengo la cuenta del ingreso a borrar...
            cuenta = self.get_object().cuenta
            # ...continuo con la ejecución normal (borra el ingreso)...
            respuesta = super().form_valid(form)
            #...Recalcula el total
            CuentaCBV.actualizarReservasCuenta(cuenta)
            return respuesta

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda borrar los datos de otros usuarios
            '''
            ingreso = self.get_object()
            if ingreso.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede borrar este ingreso.")
            
            return super().dispatch(request, *args, **kwargs)

    class IngresoUpdate(LoginRequiredMixin, UpdateView):
        model = Ingreso
        form_class = IngresoForm
        template_name = 'finanzas_app/class_based_views/ingresos/ingreso_editar.html'
        success_url = reverse_lazy('ingresos')

        def form_valid(self, form):
            # Obtengo la cuenta del ingreso a borrar...
            cuenta = self.get_object().cuenta
            # ...continuo con la ejecución normal (edita el ingreso)...
            respuesta = super().form_valid(form)
            #...Recalcula el total
            CuentaCBV.actualizarReservasCuenta(cuenta)
            return respuesta
        
        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda modificar la información de otros usuarios
            '''
            ingreso = self.get_object()
            if ingreso.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede editar este ingreso.")

            return super().dispatch(request, *args, **kwargs)

    class IngresoList(LoginRequiredMixin, ListView):
        template_name = 'finanzas_app/class_based_views/ingresos/ingresos.html'
        model = Ingreso

        def get_queryset(self):
            '''
            Sólo devuelve lo correspondiente al usuario actual
            '''
            return Ingreso.objects.filter(usuario=self.request.user.perfilusuario)
#====================Ingreso|====================#

#====================|Cuenta====================#
# Creo la clase CuentaCBV sólo por comodidad para programar
class CuentaCBV:
    def actualizarReservasCuenta(cuenta):
        if cuenta != None: 
            ingresos = Ingreso.objects.filter(cuenta=cuenta)
            egresos = Egreso.objects.filter(formaDePago__in=FormaDePago.objects.filter(cuenta=cuenta))
        else:
            ingresos = None
            egresos = None
        print('Ingresos:')
        for ingreso in ingresos:
            print(ingreso.monto)
        print('Egresos:')
        for egreso in egresos:
            print(egreso.monto)

    class CuentaCrear(LoginRequiredMixin, CreateView):
        model = Cuenta
        form_class = CuentaForm
        template_name = 'finanzas_app/class_based_views/cuentas/cuenta_crear.html'
        success_url = reverse_lazy('cuentas')

        def form_valid(self, form):
            '''
            No pido información de a qué usuario pertenece
            porque corresponde al usuario actual.
            Se agrega esta información automáticamente una 
            vez se tiene el formulario válido 
            '''

            form.instance.usuario = self.request.user.perfilusuario
            # Si el alias ya esta repetido, le agrego un número para diferenciarlo
            i = 1
            alias = form.instance.nombreAlias
            while form.instance.nombreAlias in Cuenta.objects.filter(usuario=self.request.user.perfilusuario).values_list('nombreAlias', flat=True):
                form.instance.nombreAlias = alias + f'_{i}'
                i += 1

            return super().form_valid(form)
        
    class CuentaDelete(LoginRequiredMixin, DeleteView):
        model = Cuenta
        template_name = 'finanzas_app/class_based_views/cuentas/cuenta_eliminar.html'
        success_url = reverse_lazy('cuentas')

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que los datos pertenezcan al usuario actual para
            que no pueda borrar la información de otros usuarios
            '''
            cuenta = self.get_object()
            if cuenta.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede borrar esta cuenta.")
            
            return super().dispatch(request, *args, **kwargs)

    class CuentaUpdate(LoginRequiredMixin, UpdateView):
        model = Cuenta
        form_class = CuentaForm
        template_name = 'finanzas_app/class_based_views/cuentas/cuenta_editar.html'
        success_url = reverse_lazy('cuentas')

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda modificar las cuentas de otros usuarios
            '''
            cuenta = self.get_object()
            if cuenta.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede editar esta cuenta.")
            
            return super().dispatch(request, *args, **kwargs)

    class CuentasList(LoginRequiredMixin, ListView):
        template_name = 'finanzas_app/class_based_views/cuentas/cuentas.html'
        model = Cuenta

        def get_queryset(self):
            '''
            Sólo devuelve lo correspondiente al usuario actual
            '''
            return Cuenta.objects.filter(usuario=self.request.user.perfilusuario)
#====================Cuenta|====================#

#====================|Forma de pago====================#
# Creo la clase FormaDePagoCBV sólo por comodidad para programar
class FormaDePagoCBV:
    class FormaDePagoList(LoginRequiredMixin, ListView):
        template_name = 'finanzas_app/class_based_views/formas_de_pago/formas_de_pago.html'
        model = FormaDePago

        def get_queryset(self):
            '''
            Sólo devuelve lo correspondiente al usuario actual
            '''
            return FormaDePago.objects.filter(usuario=self.request.user.perfilusuario)
        
    class FormaDePagoUpdate(LoginRequiredMixin, UpdateView):
        model = FormaDePago
        form_class = FormaDePagoForm
        template_name = 'finanzas_app/class_based_views/formas_de_pago/forma_de_pago_editar.html'
        success_url = reverse_lazy('formas_de_pago')

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda modificar las cuentas de otros usuarios
            '''
            formaDePago = self.get_object()
            if formaDePago.usuario.usuario != self.request.user:
                return HttpResponseForbidden("No puede editar esta cuenta.")
            
            return super().dispatch(request, *args, **kwargs)

    class FormaDePagoCrear(LoginRequiredMixin, CreateView):
        model = FormaDePago
        form_class = FormaDePagoForm
        template_name = 'finanzas_app/class_based_views/formas_de_pago/forma_de_pago_crear.html'
        success_url = reverse_lazy('formas_de_pago')

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            
            # 'instance' es el objeto que se está creando y que se pasará para
            # crear el formulario. Si le agrego la información de usuario, puedo
            # filtrar qué cuentas aparecen disponibles en la lista del formulario
            # llamando a FormaDePagoForm.__init__()
            if not kwargs.get('instance', None) or not kwargs['instance'].instance:
                kwargs['instance'] = FormaDePago(usuario=self.request.user.perfilusuario)
            return kwargs
    
        def form_valid(self, form):
            '''
            No pido información de a qué usuario pertenece
            porque corresponde al usuario actual.
            Se agrega esta información automáticamente una 
            vez se tiene el formulario válido 
            '''
            #form.instance.usuario = self.request.user.perfilusuario

            # Si el alias ya esta repetido, le agrego un número para diferenciarlo
            i = 1
            alias = form.instance.nombreAlias
            while form.instance.nombreAlias in Cuenta.objects.filter(usuario=self.request.user.perfilusuario).values_list('nombreAlias', flat=True):
                form.instance.nombreAlias = alias + f'_{i}'
                i += 1

            return super().form_valid(form)
        
    class FormaDePagoDelete(LoginRequiredMixin, DeleteView):
        model = FormaDePago
        template_name = 'finanzas_app/class_based_views/formas_de_pago/forma_de_pago_eliminar.html'
        success_url = reverse_lazy('formas_de_pago')

        def dispatch(self, request, *args, **kwargs):
            '''
            Verifica que pertenezca al usuario actual para
            que no pueda borrar la información de otros usuarios
            '''
            formaDePago = self.get_object()
            if formaDePago.usuario.usuario != self.request.user:
                return HttpResponseForbidden('No puede borrar esta forma de pago.')
            
            return super().dispatch(request, *args, **kwargs)
#====================Forma de pago|====================#


class ProveedoresPagoList(ListView):
    template_name = 'finanzas_app/class_based_views/proveedores_de_pago/proveedores_de_pagos.html'
    model = ProveedorPagos

class ProveedoresPagoCrear(CreateView):
    model = ProveedorPagos
    form_class = ProveedorPagosForm
    template_name = 'finanzas_app/class_based_views/proveedores_de_pago/proveedor_de_pagos_crear.html'
    success_url = reverse_lazy('proveedores_de_pagos')
    
class ProveedoresPagoUpdate(UpdateView):
    model = ProveedorPagos
    form_class = ProveedorPagosForm
    template_name = 'finanzas_app/class_based_views/proveedores_de_pago/proveedor_de_pagos_editar.html'
    success_url = reverse_lazy('proveedores_de_pagos')

class ProveedoresPagoDelete(DeleteView):
    model = ProveedorPagos
    template_name = 'finanzas_app/class_based_views/proveedores_de_pago/proveedor_de_pagos_eliminar.html'
    success_url = reverse_lazy('proveedores_de_pagos')


class Authentication:
    def logOutView(request):
        logout(request)
        return redirect(reverse_lazy('home'))


    def logInView(request):
        if request.method == "POST":
            form = LogInForm(request, data=request.POST)
                
            if form.is_valid():
                userName        = form.cleaned_data.get('username')
                userPassword    = form.cleaned_data.get('password')
                
                user = authenticate(request, username=userName, password=userPassword)
                if user is not None:
                    login(request, user)
                    return redirect(reverse_lazy('home'))


                print("...", userName)
                print("...", userPassword)
                print("Errors...", form.errors)

            return render(request, 'authenticate.html', {'form': form, 'login_attempt': True, 'failed': True})

        else:
            logInForm = LogInForm()
            return render(request, 'authenticate.html', {"form": logInForm, "login_attempt": True})


    def signUpView(request):

        if request.method == "POST":
            form = SignUpForm(request.POST)

            if form.is_valid():
                nuevoUsuario = form.save()
                PerfilUsuario(usuario = nuevoUsuario).save()
                login(request, nuevoUsuario)
                return redirect(reverse_lazy('home'))
            else:
                pass

            return render(request, 'authenticate.html', {'form': form, 'login_attempt': False, 'failed': True})
        else:
            signupForm = SignUpForm()
            return render(request, 'authenticate.html', {'form': signupForm, 'login_attempt': False})
    