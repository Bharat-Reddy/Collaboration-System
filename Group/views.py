from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from .models import Group, GroupMembership, GroupArticles
from BasicArticle.models import Articles
from BasicArticle.views import create_article, view_article
from Community.models import CommunityMembership, CommunityGroups
from django.contrib.auth.models import Group as Roles

def create_group(request):
	if request.method == 'POST':
		name = request.POST['name']
		desc = request.POST['desc']
		user = request.user
		visibility = request.POST['visibility']
		group = Group.objects.create(
			name = name,
			desc  = desc,
			visibility = visibility
			)
		role = Roles.objects.get(name='group_admin')
		obj = GroupMembership.objects.create(user=user, group=group, role=role)
		return group

def group_view(request, pk):
	try:
		group = Group.objects.get(pk=pk)
		uid = request.user.id
		membership = GroupMembership.objects.get(user=uid, group=group.pk)
	except GroupMembership.DoesNotExist:
		membership = 'FALSE'
	try:
		community = CommunityGroups.objects.get(group=pk)
		communitymembership = CommunityMembership.objects.get(user =uid, community = community.community.pk)
	except CommunityMembership.DoesNotExist:
		communitymembership = 'FALSE'
	subscribers = GroupMembership.objects.filter(group = pk).count()
	articles = GroupArticles.objects.filter(group = pk)
	users = GroupArticles.objects.raw('select  u.id,username from auth_user u join Group_grouparticles g on u.id = g.user_id where g.group_id=%s group by u.id order by count(*) desc limit 2;', [pk])
	contributors = GroupMembership.objects.filter(group = pk)
	return render(request, 'groupview.html', {'group': group, 'communitymembership':communitymembership,'membership':membership, 'subscribers':subscribers, 'contributors':contributors, 'articles':articles, 'users':users, 'community':community})

def group_subscribe(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			gid = request.POST['gid']
			group = Group.objects.get(pk=gid)
			user = request.user
			role = Roles.objects.get(name='author')
			obj = GroupMembership.objects.create(user=user, group=group, role=role)
			return redirect('group_view', pk=gid)
		return render(request, 'groupview.html')
	else:
		return redirect('login')

def group_unsubscribe(request):
	if request.method == 'POST':
		gid = request.POST['gid']
		group = Group.objects.get(pk=gid)
		user = request.user
		obj = GroupMembership.objects.filter(user=user, group=group).delete()
		return redirect('group_view', pk=gid)
	return render(request, 'groupview.html')

def group_article_create(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			status = request.POST['status']
			gid = request.POST['gid']
			group = Group.objects.get(pk=gid)
			if status=='1':
				article = create_article(request)
				obj = GroupArticles.objects.create(article=article, user=request.user, group=group)
				return redirect('article_view', article.pk)
			else:
				return render(request, 'new_article.html', {'group':group, 'status':1})
		else:
			return redirect('home')
	else:
		return redirect('login')

def manage_group(request,pk):
	group = Group.objects.get(pk=pk)
	return render(request, 'managegroup.html', {'group': group})
