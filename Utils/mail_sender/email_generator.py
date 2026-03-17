
def generate_email(record_data: dict, days_left: int) -> str:

    # The Full HTML Template
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <div style="max-width: 600px; margin: 0 auto;">
    
            <p><strong>Day {str(6 - days_left)} — {str(days_left)} Business Days Remaining</strong></p>
            
            <p><strong>Hi {record_data['Instructor']},</strong></p>
    
            <p>We are noticing that your class roster has not been submitted in the Enrollware system. Per Training Center policy, all course rosters must be entered into Enrollware and all eCards must be issued through the <a href="https://www.enrollware.com" style="color: #2D8CFF;">Enrollware.com</a> system, which you currently have access to.</p>
    
            <p>At this time, we are showing the following student information associated with an issued card:</p>
    
            <h3 style="color: #2c3e50; margin-bottom: 10px;">Student Information</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; margin-bottom: 20px;">
                <tbody>
                    <tr>
                        <th style="padding: 8px; border-bottom: 1px solid #ddd; background-color: #eee; width: 40%;">Name</th>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{record_data['Student Name']}</td>
                    </tr>
                    <tr>
                        <th style="padding: 8px; border-bottom: 1px solid #ddd; background-color: #eee;">Email</th>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><a href="mailto:{record_data['Student Email']}" style="color: #2D8CFF;">{record_data['Student Email']}</a></td>
                    </tr>
                    <tr>
                        <th style="padding: 8px; border-bottom: 1px solid #ddd; background-color: #eee;">Course</th>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{record_data['Course']}</td>
                    </tr>
                    <tr>
                        <th style="padding: 8px; border-bottom: 1px solid #ddd; background-color: #eee;">Course Completion Card Issued</th>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{record_data['Course Date']}</td>
                    </tr>
                </tbody>
            </table>
    
            <p style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #007bff;">
                Please log into Enrollware and submit the <strong>full class roster for this course as soon as possible</strong> so the records can be properly documented in accordance with Training Center and American Heart Association recordkeeping requirements.
            </p>
    
            <p>Please keep in mind that you will also need to upload the required course documentation for the class, including:</p>
            <ul style="margin-top: 0; padding-left: 20px;">
                <li style="margin-bottom: 5px;">Course Roster</li>
                <li style="margin-bottom: 5px;">Student Course Evaluations</li>
                <li style="margin-bottom: 5px;">Exam Answer Sheet</li>
                <li style="margin-bottom: 5px;">Skills Testing Checklist</li>
            </ul>
    
            <p>This matter must be completed within <strong>{str(days_left)} business days</strong> from the date of this notice. 
            Failure to submit the required roster and course documentation within that timeframe may result in your 
            <strong>AHA instructor status being deactivated</strong>, and you will be <strong>unable to teach classes 
            until a meeting is held with the Training Center.</strong></p>
    
            <p>If you have already submitted the roster or need assistance accessing the system, please let us know so we can assist.</p>
    
            <p>Thank you for your prompt attention to this matter and please let us know when this has been completed.</p>
            
            <p style="margin: 
                10px 0;">How to use enrollware system and setup account <a href="https://vimeo.com/1173821108/03c50da74a?fl=pl&fe=sh" style="color: 
                #2D8CFF;">Video Guide</a>
            </p>
    
            <br><br>
            <hr style="border: 0; border-top: 1px solid #eee;">
    
            <div style="font-size: 14px; color: #555;">
                <p>Many Blessings,</p>
    
                <p style="font-size: 18px; margin-bottom: 5px; color: #333;"><strong>𝒩𝒶𝓉𝒽𝒶𝓃𝒾𝑒𝓁 𝒮𝒽𝑒𝓁𝓁, 
                NREMT</strong></p> <p style="margin: 0;">Training Center Coordinator</p> <p style="margin: 10px 0 2px 
                0; color: #333;"><strong>Nashville TN Corporate Office</strong></p> <p style="margin: 2px 0;">640 
                Spence Lane, Ste 125</p> <p style="margin: 2px 0;">Nashville, TN 37217</p> <br> <p style="margin: 2px 
                0;">Office: <a href="tel:6895007044" style="color: #2D8CFF;">689-500-7044</a></p> <p style="margin: 
                2px 0;">Cell: <a href="tel:3529010007" style="color: #2D8CFF;">352-901-0007</a></p> <p style="margin: 
                10px 0;">Visit Us Online at <a href="https://www.codebluecprservices.com" style="color: 
                #2D8CFF;">www.codebluecprservices.com</a></p> <p style="margin-top: 15px;"> <a href="#" 
                style="background-color: #2D8CFF; color: white; padding: 8px 12px; text-decoration: none; 
                border-radius: 4px; font-weight: bold; font-size: 12px;">REQUEST A ZOOM MEETING With Nathaniel 
                Shell</a> </p> </div> </div> </body> </html>"""
    return html_content
