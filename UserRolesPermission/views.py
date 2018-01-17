from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from Community.models import CommunityMembership, CommunityArticles, CommunityGroups, RequestCommunityCreation
from BasicArticle.models import Articles
from .forms import SignUpForm
from .roles import Author
from rolepermissions.roles import assign_role
from Group.models import GroupMembership, GroupArticles
from django.contrib.auth.models import User
from workflow.models import States
from Community.models import Community
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def signup(request):
    """
    this is a sign up function for new user in the system.  The function takes
    user input, validates it, register the user , and gives an Author role to the user.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            assign_role(user, Author)
            auth_login(request, user)
            return redirect('user_dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def user_dashboard(request):
    if request.user.is_authenticated:
        mycommunities = CommunityMembership.objects.filter(user=request.user)
        page = request.GET.get('page', 1)
        paginator = Paginator(mycommunities, 5)
        try:
            communities = paginator.page(page)
        except PageNotAnInteger:
            communities = paginator.page(1)
        except EmptyPage:
            communities = paginator.page(paginator.num_pages)

        mygroups = GroupMembership.objects.filter(user=request.user)
        page = request.GET.get('page2',1)
        paginator = Paginator(mygroups, 5)
        try:
            groups = paginator.page(page)
        except PageNotAnInteger:
            groups = paginator.page(1)
        except EmptyPage:
            groups = paginator.page(paginator.num_pages)

        commarticles = CommunityArticles.objects.filter(user=request.user)
        grparticles = GroupArticles.objects.filter(user=request.user)

        pendingcommunities=RequestCommunityCreation.objects.filter(status='Request', requestedby=request.user)

        return render(request, 'userdashboard.html', {'communities': communities, 'groups':groups, 'commarticles':commarticles, 'grparticles':grparticles, 'pendingcommunities':pendingcommunities,'articlescontributed':'1500,114,106,106,107,2,133,221,783,1123,1345,1634','articlespublished':'900,350,411,502,635,5,947,1102,1400,1267,1674,1987' })
    else:
        return redirect('login')

def home(request):
	state = States.objects.get(name='publish')
	articles=Articles.objects.filter(state=state).order_by('-views')[:3]
	articlesdate=Articles.objects.filter(state=state).order_by('-created_at')[:3]
	community=Community.objects.all().order_by('?')[:3]
	return render(request, 'home.html', {'articles':articles, 'articlesdate':articlesdate, 'community':community})

def update_profile(request):
	if request.user.is_authenticated:
		if request.method == 'POST':
			first_name = request.POST['first_name']
			last_name = request.POST['last_name']
			email = request.POST['email']
			uid = request.user.id
			usr = User.objects.get(pk = request.user.id)
			usr.email=email
			usr.first_name=first_name
			usr.last_name=last_name
			usr.save()
			return redirect('user_dashboard')
		else:
			return render(request, 'update_profile.html')
	else:
		return redirect('login')

def view_profile(request):
	if request.user.is_authenticated:
		return render(request, 'myprofile.html')
	else:
		return redirect('login')

def display_user_profile(request, username):
    if request.user.is_authenticated:
        userinfo = User.objects.get(username=username)
        communities = CommunityMembership.objects.filter(user=userinfo)
        groups = GroupMembership.objects.filter(user=userinfo)
        commarticles = CommunityArticles.objects.filter(user=userinfo)
        grparticles = GroupArticles.objects.filter(user=userinfo)
        return render(request, 'userprofile.html', {'userinfo':userinfo, 'communities':communities, 'groups':groups, 'commarticles':commarticles, 'grparticles':grparticles})
    else:
        return redirect('login')


def get_users(email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.

        """

        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())





def forgot_password(request):
    args = {}

    args.update(csrf(request))
    token_generator=default_token_generator
    domain_override=None
    #context={}
    if request.method == 'POST':

        email = request.POST['email']

        email_valid=validateemailid(email)
        username=User.objects.get(email=email).username
        #user=email
        #print("success",user)
        for user in get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
                #print("user",site_name,domain)
            else:
                site_name = domain = domain_override
            context = {
                'email': email,
                'domain': '127.0.0.1:8000',
                'site_name': '127.0.0.1:8000',
                'uid': urlsafe_base64_encode(force_bytes(user)),
                'user': username,
                'token': token_generator.make_token(user),
                'protocol': 'http',
            }
        print (email_valid)
        if email_valid != -1:

           email_template='password_reset_template.html'
           emailtext = loader.render_to_string(email_template, context)
           ##emaildata=loader.get_template(email_template)
           test=send_mail("Forgot Password", emailtext , DEFAULT_FROM_EMAIL ,[email], fail_silently=False)
           print(test)
           args['email']=email
           return render(request,'password_reset_email.html',args)
        else:
           args['message']="Invalid Email Address"
           return render(request,'forgotpassword.html',args)
    return render(request,'forgotpassword.html',args)

def change_password(request,uidb64,token):
    if request.method == 'POST':
        print("suc",request.user)
        form = PasswordChangeForm(request.user, request.POST)
        if  form.is_valid():
            user = form.save()
            print("jdhh")
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return render(request,'resetpasswordsuccess.html')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'changepassword.html', {
        'form': form
    })


def change_password_success(request):

    return render(request,'resetpasswordsuccess.html')
