

class clsEmail():
            
    def sendEmail(self, kSubject, kBody):
        from config import *
        from email.mime.text import MIMEText
        from subprocess import Popen, PIPE
  
        msg = MIMEText(kBody)
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = kSubject
        p = Popen([SENDMAIL, "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())
        Popen.kill

  