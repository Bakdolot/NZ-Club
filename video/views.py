from datetime import timedelta
import hashlib

from rest_framework import request, viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import pagination
from rest_framework.views import APIView
from rest_framework import filters

from .paginations import LargeResultsSetPagination
from .serializers import *
from video.models import *
from accounts.utils import telegram_bot_sendtext
from rest_framework.generics import *
from django.db.models import Q
from django_filters import rest_framework
from django.core.management.utils import get_random_secret_key
from django.template.loader import render_to_string
from accounts.models import userProfile


# list get API
class CategoriesView(viewsets.generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class VideoTrainingView(viewsets.generics.ListAPIView):
    serializer_class = VideoTrainingSerializer
    queryset = VideoTraining.objects.all().order_by('-id')


class VideosView(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer
    # filter_backends = [rest_framework.DjangoFilterBackend, filters.SearchFilter]
    # search_fields = ['title']
    # filterset_fields = ['type', 'owner__profile__region']


    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = get_user_model().objects.get(id=self.request.user.id)
        if user:
            # queryset = Video.objects.filter(Q(is_active=True) | Q(views__in=[user])).distinct().extra(
            #     select={'ordering': '''(
            #                                     case when video_videoviews.create_at is null 
            #                                     then video_video.create_at 
            #                                     else video_videoviews.create_at end)'''},
            #     where=['''(
            #                                     case when video_videoviews.create_at is null 
            #                                     then video_video.is_top=false
            #                                     else video_video.is_top=true or video_video.is_top=false end
            #                                     ) and video_video.is_active=true'''],
            #     order_by=['''-ordering''']
            # )

            queryset = Video.objects.raw(f'''
            select vv.*
            from video_video vv 
            left join (
                select * from video_videoviews 
                where user_id={user.id}
                )q on vv.id=q.video_id 
            where (
                case when q.create_at is null 
                then vv.is_top=false
                else vv.is_top=true or vv.is_top=false end
                ) and vv.is_active=true
            order by (
                case when q.create_at is null 
                then vv.create_at 
                else q.create_at end
                ) desc;
            ''')
            
            return queryset
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class VideoDonateView(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = Video.objects.filter(status='2', type='3', is_active=True)
        return queryset


class VideoDetailView(viewsets.generics.RetrieveAPIView):
    serializer_class = VideoDetailSerializer

    def get(self, request, *args, **kwargs):
        queryset = Video.objects.all()
        video_detail = get_object_or_404(queryset, id=kwargs['id'])
        serializer = VideoDetailSerializer(video_detail,
                                           context={'request': request})
        return Response(serializer.data)


class ViewsDetailVideoView(viewsets.generics.ListAPIView):
    serializer_class = ViewsDetailVideoSerializer
    queryset = Video.objects.all()

    def get(self, request, *args, **kwargs):
        views = get_object_or_404(self.get_queryset(), id=self.kwargs['id'])
        serializer = ViewsDetailVideoSerializer(views,
                                                context={'request': request})
        return Response(serializer.data['get_views_count'])


class CommentsDetailVideoView(viewsets.generics.ListAPIView):
    serializer_class = CommentsDetailVideoSerializer
    queryset = Comment

    def get(self, request, *args, **kwargs):
        queryset = Video.objects.all()
        comments = get_object_or_404(queryset, id=self.kwargs['id'])
        serializer = CommentsDetailVideoSerializer(comments,
                                                   context={'request': request})
        return Response(serializer.data['comments'])


class VideoTop10View(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        user = get_user_model().objects.get(id=self.kwargs['user_id'])
        if user:
            queryset = Video.objects.raw(f'select * from video_video vv where vv.is_top=true and vv.id not in (select vs.video_id from video_videoviews vs where vs.user_id={user.id}) order by create_at desc')
            return queryset
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class VideoByCategoryView(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = Video.objects.filter(
            category=self.kwargs['category_id']).order_by('-create_at')
        return queryset


class VideoByOwnerView(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = Video.objects.filter(owner=self.kwargs['owner_id'])
        return queryset


class VideoSearchView(viewsets.generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = Video.objects.filter(title__icontains=self.kwargs['search'],
                                        status='2')
        return queryset


class VideoFilterView(ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = ()
    queryset = Video.objects.all()
    pagination_class = LargeResultsSetPagination
    filter_backends = [rest_framework.DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'owner__profile__region']

    # def get_queryset(self):
    #     type_video = self.request.query_params.get('type_video', '')
    #     region = self.request.query_params.get('region')
    #     queryset = Video.objects.filter(status='2')
    #     if type_video == 'all':
    #         pass
    #     elif type_video == 'donate':
    #         queryset = queryset.filter(type='3')
    #     elif type_video == 'vip':
    #         queryset = queryset.filter(type='2')
    #     if region:
    #         queryset = queryset.filter(owner__profile__region=region)
    #     return queryset


class FaqSearchView(viewsets.generics.ListAPIView):
    serializer_class = FAQSerializer

    def get_queryset(self):
        queryset = FAQ.objects.filter(question__icontains=self.kwargs['search'])
        return queryset


class FAQView(viewsets.generics.ListAPIView):
    serializer_class = FAQSerializer
    queryset = FAQ.objects.all().order_by('id').reverse()


class UserWatchedBannerView(viewsets.generics.UpdateAPIView):
    serializer_class = CreateViewBannerHistorySerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        banner = Banner.objects.get(id=request.data['banner_id'])
        user = get_user_model().objects.get(id=request.data['user_id'])
        if banner and user:
            if user not in banner.views.all():
                ViewBanner.objects.create(
                    user=user,
                    banner=banner,
                )
                banner.views.add(user)
                banner.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class BannerView(viewsets.generics.ListAPIView):
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()
    pagination_class = pagination.LimitOffsetPagination


class BannerDetailView(viewsets.generics.ListAPIView):
    serializer_class = BannerSerializer

    def get_queryset(self):
        queryset = Banner.objects.filter(id=self.kwargs['banner_id'])
        return queryset


# class BannerByBlockNumberView(viewsets.generics.ListAPIView):
#     serializer_class = BannerSerializer

#     def get_queryset(self):
#         queryset = Banner.objects.filter(block=self.kwargs['number'])
#         return queryset


# update put, patch API
class UserFullyWatchedView(viewsets.generics.UpdateAPIView):
    serializer_class = VideoUpdateDetailSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        video = Video.objects.get(id=request.data['video_id'])
        user = get_user_model().objects.get(id=request.data['user_id'])
        if video and user:
            if request.data['view']:
                bonus = 0
                for item in video.tariffs.all():
                    if item.views >= video.watched_videos.count():
                        bonus = item.price
                        break

                is_watched = video.watched_videos.filter(user_id=user.id).exists()
                if not is_watched:
                    ViewHistory.objects.create(
                        user=user,
                        bonus=bonus,
                        video=video,
                    )
                    profile = user.profile
                    profile.balance = profile.balance + bonus
                    profile.view_count = profile.view_count + 1
                    profile.save()
                    VideoViews.objects.create(user=user, video=video)
                    video.watched_videos.add(user)
                    video.save()

                if bonus == 0:
                    video.is_top = False
                

            if request.data['favorite']:
                video.favorites.add(user)
                video.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserNotFullyWatchedView(viewsets.generics.UpdateAPIView):
    serializer_class = VideoUpdateDetailSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        video = Video.objects.get(id=request.data['video_id'])
        user = get_user_model().objects.get(id=request.data['user_id'])
        if video and user:
            if request.data['view']:
                # VideoViews.objects.create(user=user, video=video)
                video.views.add(user)

            if request.data['favorite']:
                video.favorites.add(user)
                video.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UpVideoInSevenDayView(viewsets.generics.UpdateAPIView):
    serializer_class = UpVideoInSevenDaySerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        video = Video.objects.get(id=request.data['video_id'],
                                  owner=request.data['owner_id'])
        user = get_user_model().objects.get(id=request.data['owner_id'])
        if user and video and (video.create_at.date() + timedelta(
                days=2)) <= datetime.now().date():
            video.create_at = datetime.now()
            video.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# create post API
class CreateCommentView(viewsets.generics.CreateAPIView):
    serializer_class = CreateCommentSerializer
    permission_classes = [IsAuthenticated]


class CreateRequestView(viewsets.generics.CreateAPIView):
    serializer_class = CreateRequestSerializer
    permission_classes = [IsAuthenticated]


class VideoRequestServiceView(CreateAPIView):
    serializer_class = ServiceSerializer
    queryset = Services.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status.HTTP_201_CREATED)


class VideoServiceListView(ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Services.objects.filter(video_id=self.kwargs['video_id'])


class GetVideoImagesView(ListAPIView):
    serializer_class = GetVideoImagesSerializer

    def get_queryset(self):
        return VideoImage.objects.filter(video_id=self.kwargs['video_id'])


class BookingRequestView(GenericAPIView):
    serializer_class = BookingServiceRequestSerializer
    queryset = BookingServices.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        data = request.data
        booking = BookingServices.objects.get(id=serializer.data['id'])
        if 'card' == data['type']:
            payment_id = get_random_secret_key()
            g = render_to_string('yoomoney.html', {
                'recipient': settings.PAYMENT_RECIPIENT,
                'payment_id': payment_id,
                'comment': data['comment'],
                'count': data['total_price'],
                'url': 'booking_service/request/'
                })
            booking.payment_id = payment_id
            booking.save()
            return Response({
                'Booking request': serializer.data,
                'Payment': g
            })
        elif 'point' == data['type']:
            user = get_user_model().objects.get(id=request.user.id)
            user_prof = userProfile.objects.get(user=user)
            total_price = float(data['total_price'])
            if total_price > user_prof.balance:
                return Response({'enough points': "you don't have enough points"})
            user_prof.balance -= total_price
            user_prof.withdrawn_balance += total_price
            user_prof.save()
            booking.accept = True
            booking.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


class BookingServiceNotification(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        list_ob = [
            str(data['notification_type']),
            str(data['operation_id']),
            str(data['amount']),
            str(data['currency']),
            str(data['datetime']),
            str(data['sender']),
            str(data['codepro']),
            settings.NOTIFICATION_SECRET,
            str(data['label'])
        ]
        hash1 = hashlib.sha1(bytes("&".join(list_ob), 'utf-8'))
        pbhash = hash1.hexdigest()
        if data['sha1_hash'] != pbhash:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        query = BookingServices.objects.filter(accept=False)
        query = get_object_or_404(query, payment_id=data['label'])
        query.accept = True
        query.total_price = data['amount']
        query.save()
        return Response(status=status.HTTP_200_OK)


class CreateRequest2View(CreateAPIView):
    serializer_class = CreateRequest2Serializer
    queryset = Request2.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = serializer.save(owner=self.request.user)

        telegram_bot_sendtext('Пришла новая заявка на видео от пользователя '+video.owner)

        if request.FILES.getlist('images'):
            for image in request.FILES.getlist('images'):
                ad_image = VideoRequestImage(video=video, image=image)
                ad_image.save()
        else:
            return Response({'image': 'This field is required!'}, status.HTTP_403_FORBIDDEN)

        return Response(serializer.data, status.HTTP_201_CREATED)


class CreateLikeBannerView(viewsets.generics.CreateAPIView):
    serializer_class = CreateLikeBannerSerializer
    permission_classes = [IsAuthenticated]


class DeleteLikeBannerView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        like_banner = LikeBanner.objects.filter(banner_id=kwargs['id'],
                                                user=user)
        like_banner.delete()
        return Response(status.HTTP_204_NO_CONTENT)


class CreateComplaintView(viewsets.generics.CreateAPIView):
    serializer_class = CreateComplaintSerializer
    permission_classes = [IsAuthenticated]


class CreateVideoLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        video = Video.objects.get(id=request.data['id'])
        user = get_user_model().objects.get(id=request.user.id)
        if user not in video.likes.all():
            video.likes.add(user)
            video.save()
            return Response({'message': 'This user liked'},
                            status.HTTP_201_CREATED)
        return Response({'message': 'This user already liked'},
                        status.HTTP_204_NO_CONTENT)


class DeleteVideoLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        video = Video.objects.get(id=kwargs['id'])
        video.likes.remove(user)
        return Response(status.HTTP_204_NO_CONTENT)


class VideoProductImagesView(ListAPIView):
    serializer_class = ServiceImageSerializer

    def get_queryset(self):
        queryset = ServiceImage.objects.filter(service=self.kwargs.get('pk'))
        return queryset
