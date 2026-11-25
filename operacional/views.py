


from django.views.generic import FormView, TemplateView
from django.contrib.auth import get_user_model, login
from django.urls import reverse_lazy

from suapy import autenticar, SuapAuthError, SuapError

from .forms import LoginForm


User = get_user_model()


class LoginView(FormView):

    template_name = "operacional/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("sucesso")

    def form_valid(self, form):

        matricula = form.cleaned_data["matricula"]
        senha = form.cleaned_data["senha"]

        try:

            perfil = autenticar(matricula, senha)

            # Guarda os dados na sessão
            self.request.session["usuario_autenticado"] = True

            self.request.session["usuario"] = {
                "matricula": perfil.matricula,
                "nome": perfil.nome,
                "email": perfil.email,
                "campus": perfil.campus,
                "tipo_usuario": perfil.tipo_usuario,
            }

            return super().form_valid(form)

        except SuapAuthError:

            form.add_error(
                None,
                "Matrícula ou senha inválidas."
            )

            return self.form_invalid(form)

        except SuapError:

            form.add_error(
                None,
                "Não foi possível acessar o SUAP."
            )

            return self.form_invalid(form)
        
        
class SucessoView(TemplateView):
    template_name = "operacional/sucesso.html"
