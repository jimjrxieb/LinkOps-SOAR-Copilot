# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide a playbook to response for a Business Email Compromise Incident? [/INST] Sure. Here is the information requested.
Title: : Playbook for Business Email Compromise Incident (NIST Compliant)
1. Preparation: : Determine the members of the Cybersecurity Incident Response Team (CSIRT).
Core CSIRT members should be comprised of individuals responsible for cybersecurity only.
Include Information Technology roles, depending on the organization size.
The limited size of the core CSIRT is to assist with confidentiality and efficiency.
The core CSIRT may be activated often to investigate security events that may or may not result in an incident.
Assign roles and responsibilities to each member.
Determine extended CSIRT members.
This will often include Legal, Compliance, Public Relations, and Executive Leadership.
Define escalation paths.
Business email compromise incidents may start as events or as a lower impact/severity and then increase as more information is gathered. Establishing an escalation path is critical to success.
Ensure logging levels for email system components are set to appropriate levels.
90 days should be the minimum.
Ensure logging for email system components are stored in secure locations, preferably on a secondary system such as a SIEM.
2. Detection and Analysis: : Use the evidence that resulted in notification of business email compromise to determine next steps based on method of compromise.
Examples of evidence: an email from an external client saying they received a phishing email or malware, email rules that were not created by the user, a fraudulent funds transfer, etc.
Determine initial method of account compromise.
Interview impacted user to gather details on potential points of compromise.
Example questions:
Did you receive a suspicious email?
Did you enter your email credentials after clicking a link, or on a website that seemed to not accept them?
Have you downloaded any new software?
Have you received any documents via email that you weren’t expecting?
Search for phishing emails.
Search for emails with links to credential harvesting sites.
Search for potential malware on the user’s workstation.
Credential harvesters such as Mimikatz.
Keystroke recording software.
Clipboard scraping malware.
Once method of initial compromise is determined, use the Indicators of Compromise (IoCs) gathered to search the environment for other victims.
Potential query inputs: Email subject name, document name, document hash, URL from email, etc.
Review logs in email system searching for anomalies.
Login activity from unusual locations, systems, or browser fingerprints.
Compare any login anomalies to other logins with similar characteristics, such as:
Originating IP address
Concurrent login
Browser fingerprint
Assess victim email accounts to determine if sensitive information may be contained in them.
This may need to be extended to other sources these users and/or accounts have access to such as OneDrive, Google Drive, SharePoint, shared mailboxes, fileservers, etc.
If sensitive information is a possibility, consult legal counsel for next steps.
Search impacted systems for newly created users.
Ensure that all recently created users are accounted for.
3. Containment: : Reset all passwords associated with all identified victims.
Begin with email account passwords, but all accounts associated with the user should have their passwords reset or disabled.
Revoke authentication tokens for all identified victim accounts.
This should cover the email system and any other accounts that are associated with the impacted users.
If an external organization is identified during the investigation, notify the organization of any business email compromises or concerns.
Work with legal counsel to determine this process.
This will help prevent the organization’s users from being targeted again from the same compromised source.
If an external organization is identified during the investigation, block their related domains from sending email to your organization.
If malware is discovered during the investigation:
Preserve a sample of the malware.
Analyze the malware with any tools available.
Gather file hash using PowerShell “Get-Filehash” cmdlet.
Submit hash to community sources VirusTotal, Hybrid-Analysis, etc.
If community sources have seen the hash, note the malware characteristics.
Depending on results – initiation of the malware outbreak playbook may be required.
Isolate infected systems, do not power them off unless absolutely necessary.
Preserve the system(s) for further forensic investigation including log review, MFT analysis, deep malware scans, etc.
Block all associated IoCs in email system components.
URLs, domains, message-ID, etc. in spam filters, email-based antimalware, etc.
Block all associated IoCs in endpoint protection systems.
File hashes, malware identified, etc.
4. Eradication: : Preserve artifacts, systems, and relevant backups according to the sensitivity and scale of the incident.
These may be important for future forensics.
Retain copies of malicious emails and malware.
Store in a safe location, password protected.
If rebuilding or replacing physical systems, preserve physical hard disks, solid-state drives, or forensically sound images of those storage drives.
If rebuilding or replacing virtual machines, preserve a copy, full (independent) snapshot, or a backup of the system.
Preserve any volatile data that may have been collected during the identification and containment phases.
This may include log files, backups, malware samples, memory images, etc.
Once all relevant data, equipment, and/or systems have been preserved, replace, or rebuild systems accordingly.
5. Recovery: : Remediate any vulnerabilities and gaps identified during the investigation.
Reset passwords for all impacted accounts and/or create replacement accounts and leave the impacted accounts disabled permanently.
This may have been completed in a previous step but should be reviewed to ensure that all impacted accounts have been handled correctly.
Continue to monitor for malicious activity related to this incident for an extended period.
Alerts should be configured to aid in quick detection and response.
Examples: Anomalous behavior such as login activity from unusual locations.
If financial loss was incurred, consult cybersecurity insurance.
6. Lessons Learned: : Conduct a meeting after the business email compromise incident to discuss the following:
What things went well during the investigation?
What things did not go well during the investigation?
What vulnerabilities or gaps in the organization’s security status were identified?
How will these be remediated?
What further steps or actions would have been helpful in preventing the incident?
Do modifications need to be made to any of the following:
Application security
Operating System and/or Application patching procedures
Employee, IT, or CSIRT training
Email filtering policies
Multifactor Authentication
Email retention policies
Sensitive information policies and procedures related to email
Create and distribute an incident report to relevant parties.
A primary, and more technical, report should be completed for the CSIRT.
An executive summary should be completed and presented to the management team.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
