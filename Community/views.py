from django.shortcuts import render, redirect
from BasicArticle.views import create_article, view_article
# Create your views here.
from django.shortcuts import render
from BasicArticle.models import Articles
from .models import Community, CommunityMembership, CommunityArticles
from rest_framework import viewsets


# Create your views here.


def display_communities(request):
	communities=Community.objects.all()
	return render(request, 'communities.html',{'communities':communities})

def community_view(request, pk):
	try:
		community = Community.objects.get(pk=pk)
		uid = request.user.id
		membership = CommunityMembership.objects.get(user =uid, community = community.pk)
	except CommunityMembership.DoesNotExist:
		membership = 'FALSE'
	subscribers = CommunityMembership.objects.filter(community = pk).count()
	articles = CommunityArticles.objects.filter(community = pk)
	return render(request, 'communityview.html', {'community': community, 'membership':membership, 'subscribers':subscribers, 'articles':articles})

def community_subscribe(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			cid = request.POST['cid']
			community=Community.objects.get(pk=cid)
			user = request.user
			obj = CommunityMembership.objects.create(user=user, community=community)
			return redirect('community_view',pk=cid)
		return render(request, 'communityview.html')
	else:
		return redirect('login')

def community_unsubscribe(request):
	if request.method == 'POST':
		cid = request.POST['cid']
		community=Community.objects.get(pk=cid)
		user = request.user
		obj = CommunityMembership.objects.filter(user=user, community=community).delete()
		return redirect('community_view',pk=cid)
	return render(request, 'communityview.html')


def community_article_create(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			status = request.POST['status']
			cid = request.POST['cid']
			community = Community.objects.get(pk=cid)
			if status=='1':
				article = create_article(request)
				obj = CommunityArticles.objects.create(article=article, user = request.user , community =community )
				return redirect('article_view', article.pk)
			else:
				return render(request, 'new_article.html', {'community':community, 'status':1})
		else:
			return redirect('home')
	else:
		return redirect('login')


##def is_community_member(request):