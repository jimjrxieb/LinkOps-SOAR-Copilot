# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide a incident response playbook for phishing attack? [/INST] Sure. Here is the information requested.
Title: : Phishing Incident Response Playbook
1. Preparation: : Objective: Establish Contacts, Define Procedures, Gather Information to Save Time During an Incident
Communication Preparation:
Prepare a communication, ready to be published anytime, to warn your collaborators about an ongoing phishing attack. Prepare and test a clear deployment procedure as well.
Deploy Email Security Protocols:
Implement DKIM, DMARC, and SPF for all mail chains.
Implement Multi-Factor Authentication:
Ensure multi-factor authentication mechanisms are in place.
Monitor Cybersquatted Domains:
Monitor cybersquatted domains and content posted on them. Gather contact and abuse information to be prepared in case you need to use them.
Internal Contacts:
Maintain a list of all people involved in domain names registration in the company.
Maintain a list of all people accredited to make decisions on cybercrime and actions regarding phishing. If possible, have a contract mentioning you can take decisions.
External Contacts:
Establish several ways to be reached in a timely manner (24/7 if possible):
Email address, easy to remember for everyone (ex: security@yourcompany)
Web forms on your company’s website (no more than 2 clicks away from the main page)
Visible Twitter account
Maintain a list of takedown contacts in:
Hosting companies
Registry companies
Email providers
Establish and maintain contacts in CERTs ((Computer Emergency Response Team) worldwide.


Raise Awareness
Customer Awareness:
Don’t wait for phishing incidents to communicate with your customers. Raise awareness about phishing fraud, explain what phishing is and ensure your customers know you won’t ever ask them for credentials/banking information by email or phone.
Business Line Awareness:
Ensure people in business lines are aware of phishing problems and consider security a priority. Encourage good practices such as avoiding sending links (URL) to customers and using a signature stating that the company will never ask them for credential/banking information online.
Run periodic awareness phishing campaigns.
Deploy a technical solution allowing collaborators to easily report email to security teams.
Establish specific procedures for attachment and URL analysis.
2. Detection and Analysis: : Objective: Detect the Incident, determine its Scope, and Involve the Appropriate Parties
Phishing Detection
Monitor all points of contact closely (email, web forms, etc.).
Deploy spam traps and try to gather spam from partners/third parties.
Deploy active monitoring of phishing repositories, like PhishTank and Google Safe Browsing.
Monitor any specialized mailing-list or any RSS/Twitter feed reporting phishing cases.
Use automated monitoring systems on all these sources so that every detection triggers an alarm for instant reaction.
Monitor web logs to check for suspicious referrers bringing people to your website.
Phishing Attack Scoping
Determine the number of targeted users.
Search for exploited compromised accounts and identify related malicious activities.
Analyze the Phishing
Follow established analysis procedures.
Determine:
If it is a credential harvesting campaign or a malware spreading campaign.
If it is a targeted campaign or not.
Inspect message subject and body.
Use a sandbox environment to analyze malicious attachments and extract IOCs.
Analyze links, domain, and hostnames with threat intelligence services.
Check the source code of the phishing website.
Investigate email headers for interesting artifacts like originated server and sender information.
Collect Evidence
Make a time-stamped copy of the phishing web pages using tools like HTTrack. Take screenshots if necessary.
If the phishing campaign is distributing malware, refer to IRM 7 WindowsMalwareDetection.
3. Containment: : Objective: Mitigate the Attack’s Effects on the Targeted Environment
Block network IOCs discovered via the attachment/URL analysis on DNS, firewalls, or proxies.
Block the phishing campaign based on senders, subjects, or other email artifacts via email gateway.
Try to delete phishing emails from inboxes.
Apply DNS Sinkhole on the suspicious URL (optional depending on DNS architecture).
Communicate with your collaborators.
Deploy the alert/warning page with information about the current phishing attack.
4. Eradication: : Objective: Take Actions to Stop the Phishing Campaign
Change and/or temporarily block login credentials of compromised accounts.
If the phishing campaign was targeted, consider contacting law enforcement and regulators.
Consider contacting your local CERT.
5. Recovery: : Objective: Restore the System to Normal Operations
Assess the End of the Phishing Case
Ensure that the fraudulent pages and/or email addresses are down.
Keep monitoring the fraudulent URL as phishing websites can reappear.
For more details on authentication and infrastructure recovery, refer to the Large-scale malware compromise IRMXXX.
At the end of a phishing campaign, remove the associated warning page from your website.
6. Lessons Learned: : Objective: Document the Incident’s Details, Discuss Lessons Learned, and Adjust Plans and Defenses
Report
Write a crisis report available to all crisis management cell actors. Include:
Initial cause of the infection.
Actions and timelines of every important event.
What went right and wrong.
Incident cost.
Indicators of compromise.
Capitalize
Consider what preparation steps you could have taken to respond to the incident faster or more efficiently.
Update your contacts lists and add notes on the most effective ways to contact each involved party.
Consider relationships inside and outside your organization that could help with future incidents.
Collaborate with legal teams if legal action is required.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
