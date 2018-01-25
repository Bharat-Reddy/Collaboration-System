from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Feedback, Faq

def FAQs(request):
	faqs=Faq.objects.all()
	categories = Faq.objects.values('category').distinct()
	return render(request, 'FAQs.html',{'faqs':faqs,'categories':categories})

def provide_feedback(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			title = request.POST['title']
			body  = request.POST['body']
			user = request.user
			feedback = Feedback.objects.create(
				title = title,
				body  = body,
				user = user
				)
			message = 'Your feedback was successfully submitted!'
			return render(request, 'feedback.html', {'message':message})
		else:
			return render(request, 'feedback.html')
	else:
		return redirect('login')

def contact_us(request):
	return render(request, 'contact.html')
