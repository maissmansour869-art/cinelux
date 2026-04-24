from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStaffOrAdmin
from .serializers import ConfirmSerializer, HoldSerializer, ValidateTicketSerializer
from .services import BookingService


class ShowtimeSeatsView(APIView):
    def get(self, request, showtime_id):
        return Response(BookingService.seat_map(showtime_id))


class HoldBookingView(APIView):
    def post(self, request):
        serializer = HoldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(BookingService.hold_seats(request.user, serializer.validated_data["showtimeId"], serializer.validated_data["seatIds"]), status=201)


class ConfirmBookingView(APIView):
    def post(self, request):
        serializer = ConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(BookingService.confirm(request.user, serializer.validated_data["bookingGroupId"], serializer.validated_data["paymentMethod"]), status=201)


class BookingsView(APIView):
    def get(self, request):
        return Response(BookingService.list_for_user(request.user, request.query_params.get("status")))


class BookingDetailView(APIView):
    def get(self, request, booking_id):
        return Response(BookingService.get_booking(request.user, booking_id))

    def delete(self, request, booking_id):
        return Response(BookingService.cancel(request.user, booking_id))


class ValidateTicketView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request):
        serializer = ValidateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(BookingService.validate_ticket(request.user, serializer.validated_data["qrToken"]))
