from android.app import Notification, NotificationChannel, NotificationManager, Service
from android.content import Context, Intent
from android.os import Build, IBinder
from java import Override, jint, jvoid, static_proxy

CHANNEL_ID = "pfshare_running"
NOTIFICATION_ID = 1


class PFShareService(static_proxy(Service, package="pfshare")):
    @Override(jvoid, [])
    def onCreate(self):
        Service.onCreate(self)
        self._ensure_channel()
        self.startForeground(NOTIFICATION_ID, self._build_notification())

    @Override(jint, [Intent, jint, jint])
    def onStartCommand(self, intent, flags, startId):
        return Service.START_STICKY

    @Override(IBinder, [Intent])
    def onBind(self, intent):
        return None

    @Override(jvoid, [])
    def onDestroy(self):
        self.stopForeground(True)
        Service.onDestroy(self)

    def _ensure_channel(self):
        if Build.VERSION.SDK_INT >= 26:
            manager = self.getSystemService(Context.NOTIFICATION_SERVICE)
            channel = NotificationChannel(CHANNEL_ID, "PFShare", NotificationManager.IMPORTANCE_LOW)
            manager.createNotificationChannel(channel)

    def _build_notification(self):
        if Build.VERSION.SDK_INT >= 26:
            builder = Notification.Builder(self, CHANNEL_ID)
        else:
            builder = Notification.Builder(self)
        builder.setContentTitle("PFShare")
        builder.setContentText("Sharing files on your network")
        builder.setSmallIcon(self.getApplicationInfo().icon)
        builder.setOngoing(True)
        return builder.build()
