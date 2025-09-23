# ipd/room_management.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from .models import Room, Bed


class RoomManagementMixin(UserPassesTestMixin):
    """Mixin to ensure only hospital admins can manage rooms"""
    def test_func(self):
        # Allow superusers and users with HOSPITAL_ADMIN or SUPERADMIN roles
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return True
            return hasattr(self.request.user, 'role') and self.request.user.role in ['ADMIN', 'SUPERADMIN']
        return False

    def handle_no_permission(self):
        # Redirect to dashboard with error message if user doesn't have permission
        messages.error(self.request, "You don't have permission to access room management. Contact your administrator.")
        return redirect('dashboard:dashboard')


class RoomListView(LoginRequiredMixin, RoomManagementMixin, ListView):
    model = Room
    template_name = 'ipd/room_management/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 20

    def get_queryset(self):
        return Room.objects.prefetch_related('beds').order_by('floor', 'number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_rooms'] = Room.objects.count()
        context['occupied_rooms'] = Room.objects.filter(is_occupied=True).count()
        context['total_beds'] = Bed.objects.count()
        context['available_beds'] = Bed.objects.filter(available=True).count()
        return context


class RoomCreateView(LoginRequiredMixin, RoomManagementMixin, CreateView):
    model = Room
    template_name = 'ipd/room_management/room_form.html'
    fields = ['number', 'floor', 'room_type']
    success_url = reverse_lazy('ipd:room_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Room {form.instance.number} created successfully!')
        return response


class RoomUpdateView(LoginRequiredMixin, RoomManagementMixin, UpdateView):
    model = Room
    template_name = 'ipd/room_management/room_form.html'
    fields = ['number', 'floor', 'room_type']
    success_url = reverse_lazy('ipd:room_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Room {form.instance.number} updated successfully!')
        return response


class RoomDeleteView(LoginRequiredMixin, RoomManagementMixin, DeleteView):
    model = Room
    template_name = 'ipd/room_management/room_confirm_delete.html'
    success_url = reverse_lazy('ipd:room_list')

    def delete(self, request, *args, **kwargs):
        room = self.get_object()
        # Check if room has any beds or active IPD records
        if room.beds.exists():
            messages.error(request, f'Cannot delete Room {room.number}. It has beds assigned. Please delete beds first.')
            return redirect('ipd:room_list')
        
        if hasattr(room, 'ipdrecord_set') and room.ipdrecord_set.exists():
            messages.error(request, f'Cannot delete Room {room.number}. It has IPD records associated with it.')
            return redirect('ipd:room_list')
        
        messages.success(request, f'Room {room.number} deleted successfully!')
        return super().delete(request, *args, **kwargs)


class BedListView(LoginRequiredMixin, RoomManagementMixin, ListView):
    model = Bed
    template_name = 'ipd/room_management/bed_list.html'
    context_object_name = 'beds'
    paginate_by = 30

    def get_queryset(self):
        room_id = self.request.GET.get('room')
        queryset = Bed.objects.select_related('room').order_by('room__number', 'number')
        
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.all().order_by('number')
        context['selected_room'] = self.request.GET.get('room', '')
        context['total_beds'] = Bed.objects.count()
        context['available_beds'] = Bed.objects.filter(available=True).count()
        context['occupied_beds'] = Bed.objects.filter(available=False).count()
        return context


class BedCreateView(LoginRequiredMixin, RoomManagementMixin, CreateView):
    model = Bed
    template_name = 'ipd/room_management/bed_form.html'
    fields = ['room', 'number']
    success_url = reverse_lazy('ipd:bed_list')

    def form_valid(self, form):
        form.instance.available = True  # New beds are available by default
        response = super().form_valid(form)
        messages.success(self.request, f'Bed {form.instance.number} created successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.all().order_by('number')
        return context


class BedUpdateView(LoginRequiredMixin, RoomManagementMixin, UpdateView):
    model = Bed
    template_name = 'ipd/room_management/bed_form.html'
    fields = ['room', 'number', 'available']
    success_url = reverse_lazy('ipd:bed_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Bed {form.instance.number} updated successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms'] = Room.objects.all().order_by('number')
        return context


class BedDeleteView(LoginRequiredMixin, RoomManagementMixin, DeleteView):
    model = Bed
    template_name = 'ipd/room_management/bed_confirm_delete.html'
    success_url = reverse_lazy('ipd:bed_list')

    def delete(self, request, *args, **kwargs):
        bed = self.get_object()
        
        # Check if bed has active IPD records
        if hasattr(bed, 'ipdrecord_set') and bed.ipdrecord_set.filter(status='admitted').exists():
            messages.error(request, f'Cannot delete Bed {bed.number}. It has active IPD records.')
            return redirect('ipd:bed_list')
        
        messages.success(request, f'Bed {bed.number} deleted successfully!')
        return super().delete(request, *args, **kwargs)
