from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponseRedirect
from django.views.generic import FormView, DetailView, View
from django.urls import reverse_lazy

# local imports
from .forms import EnterGameIDForm

from .models import CustomUser, Game


class CustomLoginView(LoginView):
    template_name = 'game/login.html'
    redirect_authenticated_user = True


class GuestLoginView(LoginView):
    template_name = 'game/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('enter_game_id')

    def post(self, request, *args, **kwargs):
        user = CustomUser.guest_create()
        auth_login(request, user)
        return HttpResponseRedirect(self.get_success_url())


class EnterGameIDFormView(LoginRequiredMixin, FormView):
    form_class = EnterGameIDForm
    template_name = 'game/enter-game-id.html'

    def form_valid(self, form):
        game_id = form.cleaned_data['game_id']
        self.success_url = reverse_lazy('game', args=(game_id, ))
        return super().form_valid(form)


class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    template_name = 'game/game-room.html'

    def get_object(self, game_id: str):
        try:
            self.object = self.model.objects.get(
                game_id=game_id, is_end=False
            )
            if self.request.user not in [
                self.object.player1, self.object.player2
            ]:
                raise Http404
        except self.model.DoesNotExist:
            raise Http404
        return self.object

    def get(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')

        self.object = self.get_object(game_id)
        context = self.get_context_data(object=self.object, game_id=game_id)
        return self.render_to_response(context)
