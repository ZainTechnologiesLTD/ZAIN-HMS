// Persist dismissal in localStorage
document.getElementById('dismiss-2fa-banner')?.addEventListener('click', function(){
  localStorage.setItem('dismiss2faUntil', Date.now() + 7*24*60*60*1000); // 7 days
  this.closest('.alert').remove();
});
window.addEventListener('DOMContentLoaded', function(){
  const until = localStorage.getItem('dismiss2faUntil');
  if (until && Number(until) > Date.now()) {
    document.getElementById('dismiss-2fa-banner')?.closest('.alert')?.remove();
  }
});
