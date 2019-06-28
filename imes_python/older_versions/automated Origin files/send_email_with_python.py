# -*- coding: utf-8 -*-
"""
# Sending email with attachments from Gmail account  

Created on Wed Mar 13 14:55:16 2019
@author: ericmuckley@gmail.com
"""

import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

# USE THIS ACCOUNT TO SEND EMAILS:
# email: imes.data@gmail.com
# password: imes.data2019

def send_email(to_address,
               attachment_file,
               subject_text,
               boddy_text,
               from_address='imes.data@gmail.com',
               password_of_sender='imes.data2019'):
    # send an email wtith attachment using a gmail account as the sender
    # instance of MIMEMultipart 
    msg = MIMEMultipart()  
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject_text
    # attach the body with the msg instance 
    msg.attach(MIMEText(body_text, 'plain')) 
    # open the file to be sent  
    attachment = open(attachment_file, "rb") 
    # instance of MIMEBase and named as p 
    p = MIMEBase('application', 'octet-stream') 
    # To change the payload into encoded form 
    p.set_payload((attachment).read()) 
    # encode into base64 
    encoders.encode_base64(p) 
    p.add_header('Content-Disposition',
                 'attachment; filename= %s' % attachment_file) 
    # attach the instance 'p' to instance 'msg' 
    msg.attach(p) 
    # creates SMTP session 
    s = smtplib.SMTP('smtp.gmail.com', 587) 
    # start TLS for security 
    s.starttls() 
    # Authentication 
    s.login(from_address, password_of_sender) 
    # Converts the Multipart msg into a string 
    text = msg.as_string() 
    # sending the mail 
    s.sendmail(from_address, to_address, text) 
    # terminating the session 
    s.quit()






from_address = 'imes.data@gmail.com'
password_of_sender = 'imes.data2019'
to_address = 'ericmuckley@gmail.com'
subject_text = 'Message from i-moose system'
attachment_file = 'C:\\Users\\Eric\\Desktop\\chamber_image.jpg'
# use '\n' character to begin new line in email body text
body_text = ('Dear researcher, \n'
             'This is a test message from the i-moose system at CNMS.\n'
             '\n'
             'There should be a test file attached to this email.\n'
             'In the future, this attachment will be an Origin report of\n'
             'recent experimental results.\n'
             '\n'
             'Stay tuned for more updates coming soon.\n'
             '\n'
             'Regards,\n'
             'i-moose')


send_email(to_address,
           attachment_file,
           subject_text,
           body_text,
           from_address='imes.data@gmail.com',
           password_of_sender='imes.data2019')