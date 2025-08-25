# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide a incident response playbook for phishing attack? [/INST] Sure. Here is the information requested.
Title: : Phishing Incident Response Playbook
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Develop Policies and Procedures:
Establish a clear incident response policy.
Create and maintain a phishing-specific response procedure.
Incident Response Team:
Ensure that the incident response team is trained and aware of their roles.
Conduct regular phishing simulation exercises.
Reinforce Training Programs Regarding Suspected Phishing Attacks. Key Suspicious Indicators May Include:
misspellings in the message or subject
phony-seeming sender names, including mismatches between display name and email address
personal email addresses for official business (e.g., gmail or yahoo emails from business colleagues)
malicious or suspicious links
receiving an email or attachment they were not expecting but from someone they know (contact sender before opening it)
reporting suspicious activity to IT or security
Tools and Resources:
Ensure that email filtering and security tools are up-to-date.
Implement phishing detection technologies.
Maintain contact lists for internal and external communication.

Customize communication steps for phishing.
Specify tools and procedures (including who must be involved) for each step.
Escalate Incident and Communicate with Leadership per procedure
Document Incident per Procedure (and Report)
Communicate with Internal and External Legal Counsel per procedure, including discussions of compliance, risk exposure, liability, law enforcement contact, etc.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 Incident Identification
Monitoring and Alerts: Implement monitoring systems to detect phishing attempts.
Employee Reports: Encourage employees to report suspicious emails immediately. Provide clear instructions on how to report these incidents.
2.2 Scope the Attack
Determine the total number of impacted users.
Understand user actions in response to the phishing email 
Find the potentially related activity on social media and any suspicious emails. Check:
social media
any possibly suspicious emails
emails with links to external and unknown URLs
non-returnable or non-deliverable emails
any kind of notification of suspicious activity
2.3 Analyze the Message Using a Safe Device
Analyze the message using a safe device (i.e., do not open messages on a device with access to sensitive data or credentials as the message may contain malware). Determine:
who received the message
who was targeted by the message 
email address of the sender
subject line
message body
attachments (do not open attachments except according to established procedures)
links, domains, and hostnames (do not follow links except according to established procedures)
email metadata including message headers
sender information from the 'from' field and the X-authenticated user header
all client and mail server IP addresses
note "quirks" or suspicious features
2.4 Analyze Links and Attachments
Analyze links and attachments. Specify tools and procedure:
use passive collection such as nslookup and whois to find IP addresses and registration information
find related domains using OSINT on email addresses and other registration data
submit links, attachments, and/or hashes to VirusTotal
submit links, attachments, and/or hashes to a malware sandbox such as Cuckoo, Hybrid Analysis, Joe Sandbox, or VMray.
2.5 Categorize the Type of Attack
Categorize the type of attack. 
Determine the severity. Consider:
whether public or personal safety is at risk
whether personal data (or other sensitive data) is at risk
any evidence of attacker identity 
number of affected assets
preliminary business impact
whether services are affected
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Plan Remediation Events: Coordinate steps with appropriate teams.
Contain Affected Accounts:
Change login credentials.
Reduce access to critical services, systems, or data until investigation is complete.
Reinforce multi-factor authentication (MFA).
Block Malicious Activity:
Block malicious domains using DNS, firewalls, or proxies.
Block messages with similar characteristics using email gateways or services.
Forensic Measures:
Implement forensic hold or retain forensic copies of messages.
Purge related messages from other user inboxes or Otherwise Make Inaccessible.
Consider mobile device containment measures such as wiping via mobile device management (MDM). Balance against investigative/forensic impact.
Increase Detection Alert Level: Enhance monitoring, particularly from related accounts, domains, or IP addresses.
Consider Outside Security Assistance to support investigation and remediation.
Confirm Software Upgrades: Ensure relevant software upgrades and anti-malware updates on assets.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
Remove Phishing Emails: Use email filtering tools to delete the phishing email from all mailboxes.
Scan and Clean Systems: Perform a thorough scan of affected systems.
Patch Vulnerabilities: Identify and patch any vulnerabilities exploited during the phishing attack.
5. Recovery: : Objective: Restore the system to normal operations.
Launch Business Continuity/Disaster Recovery Plan(s) if compromise involved business outages: e.g., consider migration to alternate operating locations, fail-over sites, backup systems.
Restore Systems: Restore systems to their normal state using backups if necessary.
Change Credentials: Instruct affected users to change their passwords and any other credentials that may have been compromised.
Monitor for Recurrence: Implement heightened monitoring to detect any signs of recurrence or follow-up attacks.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Documentation
Incident Report: Document all actions taken during the incident response, including detection, containment, eradication, and recovery efforts.
Timeline: Create a detailed timeline of events from the initial detection to the final recovery.
Lessons Learned
Post-Incident Review: Conduct a meeting with the incident response team and other stakeholders to review the incident and response efforts.
Identify Gaps: Identify any gaps in the response process and areas for improvement.
Update Procedures: Update incident response procedures and training materials based on lessons learned.
Reporting
Internal Reporting: Prepare a detailed report for internal stakeholders, including senior management.
External Reporting: Report the incident to regulatory bodies, partners, and affected customers as required.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
