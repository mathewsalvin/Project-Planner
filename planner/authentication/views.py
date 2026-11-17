from django.shortcuts import render

from rest_framework.views import APIView

from django.core.exceptions import ValidationError

from django.contrib.auth import authenticate

from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ProfileSerializer

from decouple import config

from planner.utils import send_mail

import threading

class LoginView(APIView):

    def post(self,request,*args,**kwargs):

        username = request.data.get('username')

        password = request.data.get('password')

        try:

            if not username or not password:

             raise ValidationError("Username and password are required.")

        except ValidationError as e:

           data={'error':e}

           return Response(data,status=400)

        user = authenticate(username=username,password=password)

        if user :

            refresh_token=RefreshToken.for_user(user)

            access_token=refresh_token.access_token

            data={'access':str(access_token),'refresh':str(refresh_token)}

            return Response(data,status=200)

        data ={"message":"invalid credentials"}

        return Response(data,status=401)


class RegisterView(APIView):

    serializer_class = ProfileSerializer

    def post(self,request,*args,**kwargs):

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        username = serializer.validated_data.get('username')

        password = serializer.validated_data.get('password')

        profile = serializer.save()

        profile.email = username

        profile.set_password(password)

        profile.save()

        recipient = profile.email

        subject = 'Welcome Abroad, Sweet Moments Await at CakeTales!'

        template = 'emails/registration.html'

        context = {
            'name': profile.first_name,
            'email': recipient,
            'login_url': config('LOGIN_URL'),
        }

        # send_mail(recipient, subject, template, context)

        thread = threading.Thread(target=send_mail,args=(recipient, subject, template, context))

        thread.start()

        

        data = {"message": "user created successfully"}

        return Response(data, status=201)