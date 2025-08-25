# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate a web application attack incident response playbook? [/INST] Sure. Here is the information requested.
Title: : Web application attack - Incident Response Playbook
1. Preparation: : Determine the members of the Cybersecurity Incident Response Team (CSIRT).
The core CSIRT members should be comprised of individuals responsible for cybersecurity only.
This may include some members of Information Technology roles, depending on the organization size.
The limited size of the core CSIRT is to assist with confidentiality and efficiency.
The core CSIRT may be activated often to investigate security events that may or may not result in an incident.
Assign roles and responsibilities to each member.
Determine extended CSIRT members.
This will often include Legal, Compliance, Public Relations, and Executive Leadership.
Define escalation paths.
Incidents may start as events, or as a lower impact/severity and then increase as more information is gathered. Establishing an escalation path is critical to success.
Document third-party web-hosting contacts.
Ensure logging levels for account login system components are set to appropriate levels.
90 days should be the minimum.
Ensure logging for account login system components are stored in secure locations, preferably on a secondary system such as a SIEM.
Ensure that web application backups are functioning as expected.
2. Detection and Analysis: : If the web application is hosted on another service (GoDaddy, HostGator, Ionos, local hosting company, etc.), contact the hosting service to report the issue.
Inquire as to any recent security issues in their environment.
Inquire about any potential logs that they may possess.
Obtain these logs and preserve them ASAP.
Use the evidence that resulted in notification of compromise to determine next steps based on method of compromise.
Examples of evidence: abnormal behavior in the web application, notification of compromise from an outside source, client report of anomalous or malicious behavior related to the web application, etc.
Method of compromise examples: exploited vulnerability in web application, credential harvesting phish, credential scraping from local systems, brute forced password, etc.
Determine initial method of account compromise. This will be limited to those with web application management/administrative access.
Interview impacted user to gather details on potential points of compromise.
Example questions:
Did you receive a suspicious email?
Did you enter your email credentials after clicking a link, or on a website that seemed to not accept them?
Have you downloaded any new software?
Have you received any documents via email that you weren’t expecting?
Have you noticed abnormal actions on your workstation?
Search for phishing emails.
Phishing emails are the most common method for credential theft.
Search for emails with links to credential harvesting sites.
Search the user’s web history to determine if any potentially malicious sites were visited.
Search for potential malware on the user’s workstation.
Credential harvesters such as Mimikatz.
Keystroke recording software.
Clipboard scraping malware.
Once the method of initial compromise is determined, use the Indicators of Compromise (IoCs) gathered to search the environment for other victims.
Potential query inputs for email system: Email subject name, document name, document hash, URL from email, etc.
Potential query inputs for SIEM or log searches: IP addresses, URLs, workstation names, etc.
Review logs in account login systems searching for anomalies.
Login activity from unusual locations, systems, or browser fingerprints.
Note all systems accessed by the attacker if possible.
Assess victim accounts to determine if sensitive information may be contained in them or if they have access to sensitive information on centralized storage such as fileservers.
This may need to be extended to other sources these users and/or accounts have access to such as OneDrive, Google Drive, SharePoint, shared mailboxes, fileservers, etc.
If sensitive information is a possibility, consult legal counsel for next steps.
Use the information gathered to determine what sensitive information could’ve been accessed by the attacker.
If logs are unavailable, assume all accessible data was accessed by the attacker.
If account compromise has been ruled out, proceed to investigate potential web application vulnerabilities that may have been exploited.
Perform a security scan.
Review vendor notifications of security issues.
Review community sourced threat intelligence related to the components in the web application.
3. Containment: : If management or administrative account compromise has been determined:
Reset all passwords associated with the management and administration of the web application.
Begin with the known compromised account passwords (if determined).
Enable Multi-Factor authentication anywhere possible for the impacted account(s).
Disable or reset alternative authentication methods such as certificates.
Revoke authentication tokens for all management/administrative account(s).
If an external organization is identified during the investigation, notify the organization of any compromises or concerns.
Work with legal counsel to determine this process.
This will help prevent the organization’s users from being targeted again from the same compromised source.
If malware is discovered during the investigation:
Preserve a sample of the malware.
Analyze the malware with any tools available.
Gather file hash using PowerShell “Get-Filehash” cmdlet.
Submit hash to community sources VirusTotal, Hybrid-Analysis, etc.
If community sources have seen the hash, note the malware characteristics.
Isolate infected systems, do not power them off unless absolutely necessary.
Preserve the system(s) for further forensic investigation including log review, MFT analysis, deep malware scans, etc.
Block all associated IoCs in the email system, firewall, and other security components such as endpoint protection systems.
URLs, domains, message-ID, etc. in spam filters, email-based antimalware, etc.
File hashes, malware identified, IP addresses identified, etc.
Preserve a copy of any existing web application code that may be compromised and/or altered maliciously.
4. Eradication: : Compare current web application code to a known-good copy to determine if any malicious additions have been removed.
If systems were determined to be compromised with malware or by other means:
Preserve artifacts, systems, and relevant backups according to the sensitivity and scale of the incident. These may be important for future forensics.
If rebuilding or replacing physical systems, preserve physical hard disks, solid-state drives, or forensically sound images of those storage drives.
If rebuilding or replacing virtual machines, preserve a copy, full (independent) snapshot, or a backup of the system.
Preserve any volatile data that may have been collected during the identification and containment phases.
This may include log files, code samples, backups, malware samples, memory images, etc.
Review and monitor logs to ensure that the compromise has been entirely contained.
5. Recovery: : Replace potentially compromised web application code with a known-good copy.
This may be completed by removing code anomalies or from restoring a known-good copy.
Review current web application code to ensure that all code anomalies have been removed.
This should be a new review, preferably by a different individual than the one who performed the review in Eradication step 1.
Restore web application functionality.
Restore impacted systems from a clean backup taken prior to infection if these backups are available.
For systems not restorable from backup, rebuild the machines from a known good image or from bare metal.
Remediate any vulnerabilities and gaps identified during the investigation.
Reset passwords for all impacted accounts and/or create replacement accounts and leave the impacted accounts disabled permanently.
Continue to monitor for malicious activity related to this incident for an extended period.
Alerts should be configured to aid in quick detection and response.
6. Lessons Learned: : Conduct a meeting after the incident to discuss the following:
What things went well during the investigation?
What things did not go well during the investigation?
What vulnerabilities or gaps in the organization’s security status were identified?
How will these be remediated?
What further steps or actions would have been helpful in preventing the incident?
Review and update security measures:
Change control practices
Code review practices
Authentication practices
Multi-Factor Authentication
Password complexity and use
Privileged account access
Network segmentation
Firewall configuration
Application security
Operating System and/or Application patching procedures
Employee, IT, or CSIRT training
Create and distribute an incident report to relevant parties.
A primary, and more technical, report should be completed for the CSIRT.
An executive summary should be completed and presented to the management team.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
