from celery import shared_task
from datetime import date
from .models import Client, ClientPause

@shared_task
def auto_activate_clients():
    today = date.today()
    paused_clients = ClientPause.objects.filter(
        program_pause_reactivate_on=today,
        type='Paused'
    )

    for pause in paused_clients:
        client = pause.client

        # Update client as active
        client.paused = False
        client.save()

        # Create activation row
        ClientPause.objects.create(
            client=client,
            user=pause.user,
            subscription_id=pause.subscription_id,
            type='Activated',
            paused_from=None,
            paused_to=None,
            no_of_days=(today - pause.paused_from).days,
            notes='Auto-activated',
            program_pause_reactivate_on=today,
            program_end_date=pause.program_end_date,
            program_end_date_changed=pause.program_end_date_changed - (pause.paused_to - today)
        )

        # Update Client
            client.paused = False
            client.program_end_date = new_end
            client.save()

            # Update PauseLimit
            try:
                limit = ClientPauseLimit.objects.get(client=client)
                limit.no_of_paused_days += pause_days
                limit.no_of_pause_days_rem -= pause_days
                limit.no_of_pauses_taken += 1
                limit.no_of_pause_rem -= 1
                limit.save()
            except ClientPauseLimit.DoesNotExist:
                pass

            # Update MeetingsTDC
            MeetingsTDC.objects.filter(client=client, status=False).update(
                meeting_date=models.F('meeting_date') + timedelta(days=pause_days),
                dietitian_id=pause.user.id
            )

            # Remove old Weekly Meetings
            WeeklyMeeting.objects.filter(client=client, status=False).delete()

            # Create new Saturdays
            def get_saturdays(start_date, end_date):
                sats = []
                while start_date <= end_date:
                    if start_date.weekday() == 5:
                        sats.append(start_date)
                    start_date += timedelta(days=1)
                return sats

            saturdays = get_saturdays(today + timedelta(days=1), new_end)

            for week_no, sat in enumerate(saturdays, start=1):
                WeeklyMeeting.objects.create(
                    client=client,
                    dietitian_id=pause.user.id,
                    week_no=week_no,
                    meeting_date=sat,
                    status=False
                )

        self.stdout.write(self.style.SUCCESS('✅ Clients auto reactivated successfully.'))
