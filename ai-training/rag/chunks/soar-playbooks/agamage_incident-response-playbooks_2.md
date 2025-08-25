# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide a Incident Response Playbook for Handling Fraudulent Scam Incidents? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Handling Fraudulent Scam Incidents
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Legitimate Domains List:
Maintain an up-to-date list of all legitimate domains belonging to your company to prevent confusion and ensure legitimate sites are not mistakenly taken down.
Prepared Warning Page:
Develop and host a webpage that can be quickly deployed to warn customers about ongoing fraudulent scam attacks. Test the deployment process regularly to ensure it works smoothly when needed.
Takedown Email Forms:
Create standardized takedown email templates in multiple languages. Pre-approve these forms with legal and compliance teams to expedite the takedown process when a scam is detected.
Communication Channels:
Establish multiple channels for reporting scams, including:
An easy-to-remember email address (e.g., security@yourcompany.com).
Web forms on your company’s website, located no more than two clicks from the main page.
A visible and active Twitter account for quick communication.
Ensure all email communications are secured with DKIM, DMARC, and SPF to prevent spoofing.
Contacts:
Maintain a list of all individuals authorized to make decisions on cybercrime incidents, regularly updating their contact information and decision-making authority.
Maintain a list of contacts at hosting companies, registrars, registry companies, and email providers for quick takedown requests.
Establish relationships with CERTs worldwide for additional support during incidents.
Customer Awareness:
Proactively raise awareness among customers about different types of scams through regular updates on your website, social media channels, and newsletters. Educate them on how to recognize scams and assure them that the company will never contact them for sensitive information via email.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve appropriate parties.
Fraudulent Scam Detection:
Closely monitor all points of contact, including email, web forms, and social media, for signs of fraudulent activity.
Regularly check cybersquatted domains and the content posted on them. Gather contact and abuse information to be prepared for takedown requests.
Monitor social media accounts for impersonation of your top management or misuse of your trademark.
Deploy spam traps to gather fraudulent emails from partners or third parties.
Actively monitor scam repositories and specialized mailing lists. Use automated systems to trigger alarms for immediate response when fraudulent activity is detected.
Involve Appropriate Parties:
Contact internal decision-makers immediately upon detecting a scam. Ensure the decision to act on the fraudulent email address is made quickly, ideally within minutes.
Collect Evidence:
Collect samples of fraudulent emails, including headers, to identify the real sender’s IP address. Use dedicated corporate equipment to interact with or investigate the scammer. If necessary, consult resources like SpamCop for guidance on collecting email headers.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Spread Information:
Share the fraudulent email content on spam/fraud reporting websites, with partners, and through reporting tools.
Communicate with Customers:
Inform customers about the scam by deploying the prepared warning page on your website. For frequent incidents, maintain a page with comprehensive information about various types of scams.
Block Leakage Vectors:
Add URLs used in the scam to your Blackhole DNS, proxies, and firewall blocklists to prevent further access.
Suspend Insider Access:
If an insider is involved, suspend their credentials (both logical and physical) after coordinating with HR and legal teams. Isolate the computing systems used for data disclosure by disconnecting power and batteries (for laptops) to preserve forensic evidence.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
Remove Fraudulent Content:
Contact owners of compromised websites hosting fraudulent pages, explain the fraud, and request removal of the content. Emphasize the need for improved security to prevent future incidents.
Contact hosting companies of cybersquatted domains and send takedown requests to abuse@hostingcompany, following up with phone calls if necessary.
Shut Down Fraudulent Accounts:
Contact email hosting companies to shut down fraudulent accounts, providing copies of the fraudulent emails as evidence. Also, contact social media platforms to take down fraudulent accounts.
Block Email Exchanges:
Block email exchanges with the scammer by updating email filters to block emails from the fraudulent accounts.
Persistent Follow-Up:
If no action is taken, follow up regularly and involve local CERTs if necessary to expedite the takedown process.
5. Recovery: : Objective: Restore the system to normal operations.
Assess End of the Case:
Ensure the fraudulent email address has been shut down and continue monitoring any associated fraudulent websites. Remove the warning page from your website once the scam campaign ends.
System Restoration:
Fully restore compromised systems to normal operations using clean backups or rebuild from known good images. Inform employees about the issue to raise awareness and reinforce security practices.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Report:
Write a comprehensive crisis report covering the initial cause of the incident, actions taken, timelines, successes, failures, incident cost, and indicators of compromise. Share the report with all involved actors and present an executive summary to management.
Capitalize:
Reflect on preparation steps for a faster or more efficient response. Update contact lists with notes on effective ways to contact each party. Strengthen internal and external relationships for future incidents. Improve DKIM, SPF, and DMARC filters. Collaborate with legal teams if legal action is required.
Review and update security measures, such as network segmentation, firewall configuration, application security, OS/application patching procedures, and training programs. Conduct a post-incident review meeting to discuss what went well, what did not, and how to prevent future incidents.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
