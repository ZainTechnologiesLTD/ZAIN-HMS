from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Nurse, Department, NurseSchedule, NurseLeave
from .forms import NurseForm, NurseScheduleForm, NurseLeaveForm

class NurseListView(LoginRequiredMixin, ListView):
    model = Nurse
    template_name = 'nurses/nurse_list.html'
    context_object_name = 'nurses'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        department = self.request.GET.get('department')
        shift = self.request.GET.get('shift')
        search = self.request.GET.get('search')

        if department:
            queryset = queryset.filter(department__id=department)
        if shift:
            queryset = queryset.filter(shift=shift)
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        return context

class NurseDetailView(LoginRequiredMixin, DetailView):
    model = Nurse
    template_name = 'nurses/nurse_detail.html'
    context_object_name = 'nurse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedules'] = self.object.schedules.all()[:5]
        context['leaves'] = self.object.leaves.all()[:5]
        return context

class NurseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Nurse
    form_class = NurseForm
    template_name = 'nurses/nurse_form.html'
    success_url = reverse_lazy('nurse_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Nurse profile created successfully!')
        return super().form_valid(form)

class NurseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Nurse
    form_class = NurseForm
    template_name = 'nurses/nurse_form.html'
    success_url = reverse_lazy('nurse_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Nurse profile updated successfully!')
        return super().form_valid(form)

class NurseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Nurse
    template_name = 'nurses/nurse_confirm_delete.html'
    success_url = reverse_lazy('nurse_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Nurse profile deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Schedule Views
class ScheduleCreateView(LoginRequiredMixin, CreateView):
    model = NurseSchedule
    form_class = NurseScheduleForm
    template_name = 'nurses/schedule_form.html'

    def form_valid(self, form):
        form.instance.nurse_id = self.kwargs['nurse_id']
        messages.success(self.request, 'Schedule created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('nurse_detail', kwargs={'pk': self.kwargs['nurse_id']})

class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = NurseSchedule
    form_class = NurseScheduleForm
    template_name = 'nurses/schedule_form.html'

    def get_success_url(self):
        return reverse_lazy('nurse_detail', kwargs={'pk': self.object.nurse.id})

# Leave Management Views
@login_required
def leave_request(request, nurse_id):
    nurse = get_object_or_404(Nurse, id=nurse_id)
    
    if request.method == 'POST':
        form = NurseLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.nurse = nurse
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('nurse_detail', pk=nurse_id)
    else:
        form = NurseLeaveForm()
    
    return render(request, 'nurses/leave_form.html', {'form': form, 'nurse': nurse})

@login_required
def approve_leave(request, leave_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to approve leaves!')
        return redirect('nurse_list')

    leave = get_object_or_404(NurseLeave, id=leave_id)
    leave.status = 'approved'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'Leave approved successfully!')
    return redirect('nurse_detail', pk=leave.nurse.id)

@login_required
def reject_leave(request, leave_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to reject leaves!')
        return redirect('nurse-list')

    leave = get_object_or_404(NurseLeave, id=leave_id)
    leave.status = 'rejected'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'Leave rejected successfully!')
    return redirect('nurse_detail', pk=leave.nurse.id)