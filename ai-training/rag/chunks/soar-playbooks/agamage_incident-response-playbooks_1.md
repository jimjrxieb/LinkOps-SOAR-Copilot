# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an incident response playbook for following attack details. The Havex malware attack, attributed to the Russian APT group "Energetic Bear" (Dragonfly), was a sophisticated cyber espionage campaign discovered in 2013 targeting critical infrastructure sectors such as energy, aviation, pharmaceutical, defense, and petrochemical. Utilizing advanced techniques including supply chain compromises, watering hole attacks, and spear phishing, Havex employed a Remote Access Trojan (RAT) and an OPC scanning module to infiltrate and map industrial control systems (ICS) networks. The campaign exploited legitimate software downloads from compromised vendor websites and leveraged browser vulnerabilities via exploit kits. This attack highlighted the vulnerabilities in ICS environments, the importance of robust cybersecurity measures. [/INST] Sure. Here is the information requested.
Title: : Incident response playbook for about potential attack similar to Havex malware incident
1. Preparation
1. Preparation: : Objective: Establish Contacts, Define Procedures, Gather Information to Save Time During an Incident

Internal Preparation
Communication Plan:
Prepare a communication strategy for informing stakeholders about potential attack similar to Havex malware incidents.
Test and refine the deployment procedure for incident notifications.
Deploy Security Protocols:
Implement and regularly update DKIM, DMARC, and SPF for email security.
Enforce multi-factor authentication (MFA) for all critical systems.
Monitor Threat Landscape:
Continuously monitor cybersquatted domains and content posted on them.
Gather contact and abuse information for quick takedown requests.
Internal Contacts
Maintain an updated list of personnel involved in domain registration and cybersecurity decision-making.
Ensure contracts or agreements allow for rapid decision-making in case of a cyber incident.
External Contacts
Establish and maintain 24/7 contact channels:
Dedicated email (e.g., security@yourcompany)
Web forms on the company's website (easily accessible from the main page)
Visible social media accounts (e.g., Twitter)
Maintain a list of takedown contacts in:
Hosting companies
Registry companies
Email providers
Establish and maintain contacts with CERTs worldwide for assistance.
Awareness and Training
Customer Awareness:
Educate customers about phishing and malware risks, emphasizing that the company will never request credentials or sensitive information via email or phone.
Internal Awareness:
Conduct periodic phishing and malware awareness campaigns.
Implement a reporting mechanism for suspicious emails and activities.
Establish procedures for safe handling and analysis of attachments and URLs.
2. Detection and Analysis: : Objective: Detect the Incident, Determine Its Scope, and Involve the Appropriate Parties
Detection
Monitor Entry Points:
Continuously monitor email, web forms, and other points of contact.
Deploy spam traps and gather spam samples from partners and third parties.
Active Monitoring:
Use phishing repositories like PhishTank and Google Safe Browsing.
Monitor specialized mailing lists, RSS feeds, and Twitter for phishing reports.
Employ automated monitoring systems to trigger alerts for immediate response.
Web Logs:
Check for suspicious referrers in web logs that might indicate phishing redirects.
Scoping the Attack
Assess Impact:
Determine the number of targeted users.
Identify compromised accounts and related malicious activities.
Analyzing the Malware
Follow Analysis Procedures:
Identify if the campaign is for credential harvesting or malware distribution.
Determine if it is targeted or broad-based.
Inspect Messages and Attachments:
Use sandbox environments to analyze attachments and extract Indicators of Compromise (IOCs).
Utilize threat intelligence services to analyze links, domains, and hostnames.
Examine email headers for server and sender artifacts.
Evidence Collection
Document Phishing Pages:
Use tools like HTTrack to make time-stamped copies of phishing web pages.
Capture screenshots and save copies of all related pages.
3. Containment: : Objective: Mitigate the Attack’s Effects on the Targeted Environment
Block IOCs:
Block network indicators on DNS, firewalls, or proxies.
Filter emails based on identified malicious senders, subjects, or other artifacts.
Purge Malicious Emails:
Attempt to delete phishing emails from user inboxes.
DNS Sinkhole:
Apply DNS sinkhole for suspicious URLs if applicable.
Communication:
Inform collaborators about the ongoing attack.
Deploy alert/warning pages with information about the current phishing attack.
4. Eradication: : Objective: Remove the Threat
Credential Management:
Change and/or temporarily block compromised account credentials.
Law Enforcement and Regulators:
If targeted, consider contacting law enforcement and regulatory bodies.
Patch Vulnerabilities:
Identify and patch any vulnerabilities exploited by Havex.
CERT Coordination:
Engage with local CERT for additional support and information sharing.
5. Recovery: : Objective: Restore the System to Normal Operations
Ensure Remediation:
Verify that fraudulent pages and email addresses are taken down.
Continue monitoring the fraudulent URL to ensure it does not reappear.
Infrastructure Recovery:
Follow specific procedures for recovering authentication and infrastructure, referencing large-scale malware compromise guidelines.
System Validation:
Validate the integrity and functionality of all ICS and related systems before returning to normal operations.
Remove Warning Pages:
After confirming the end of the phishing campaign, remove associated warning pages from the website.
6. Lessons Learned: : Objective: Document the Incident’s Details, Discuss Lessons Learned, and Adjust Plans and Defenses
Reporting
Crisis Report:
Document the initial cause, actions, timelines, successes, failures, and cost of the incident.
Share the report with all relevant crisis management cell actors.
Post-Incident Review
Improve Preparedness:
Assess preparation steps to enhance future incident response efficiency.
Update contact lists with notes on effective communication methods.
Identify useful relationships within and outside the organization for future incidents.
Security Enhancements:
Implement additional security measures based on lessons learned.
Review and update security policies and procedures regularly.
Legal Considerations:
Collaborate with legal teams if legal action is necessary.

This playbook provides a detailed, NIST-compliant framework for handling Havex malware attacks, ensuring preparedness, effective response, and continuous improvement.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
