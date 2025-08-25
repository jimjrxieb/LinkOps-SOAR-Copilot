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
Maintain an up-to-date list of all legitimate domains belonging to your company to prevent false takedown procedures on legitimate sites.
Prepared Warning Page:
Create a webpage hosted on your infrastructure, ready to be published at any time, to warn customers about ongoing fraudulent scam attacks.
Develop and test a clear deployment procedure for this warning page.
Takedown Email Forms:
Prepare standard takedown email forms in several languages to expedite communication with hosting companies, registrars, and email providers during the takedown process.
Communication Channels:
Establish multiple contact methods for timely reporting (24/7 if possible):
Easy-to-remember email address (e.g., security@yourcompany).
Web forms on the company’s website, no more than 2 clicks from the main page.
Visible and active Twitter account.
Deploy DKIM, DMARC, and SPF to all mail chains to enhance email security.
Contacts:
Internal Decision Makers:
Maintain a list of all individuals accredited to make decisions on cybercrime and incident response.
External Contacts:
Maintain a list of takedown contacts in hosting companies, registrars, registry companies, and email providers.
Establish and maintain contacts in CERTs worldwide for assistance during incidents.
Customer Awareness:
Raise customer awareness proactively about different types of scams (e.g., lottery scams, 419 scams).
Educate customers that the company will never contact them for such matters by email.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve appropriate parties.
Fraudulent Scam Detection:
Monitor all points of contact closely (email, web forms, etc.).
Monitor cybersquatted domains and content for signs of fraudulent use.
Monitor social media for accounts usurping your top management or trademark.
Deploy spam traps to gather fraudulent emails from partners/third parties.
Actively monitor scam repositories (e.g., 419scam).
Use automated monitoring systems on these sources to trigger alarms for instant reaction.
Involve Appropriate Parties:
Contact decision-makers immediately upon detecting a scam campaign.
Ensure a decision to act on the fraudulent email address is taken as soon as possible, ideally within minutes.
Collect Evidence:
Collect samples of fraudulent emails, including email headers.
Collect several emails to check for the real sender’s IP address, aiding in determining if the campaign is sent from a single machine or a botnet.
Use dedicated corporate equipment to interact with or investigate the scammer.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Spread Information:
Share the fraudulent email content on spam/fraud reporting websites, partners, and tools.
Communicate with your customers about the scam.
Add the URLs used in the scam to your Blackhole DNS, proxies, and firewall’s blocklist.
Deploy Alert/Warning Page:
If the brand is impacted, deploy the prepared warning page with information about the current scam attack.
For frequent incidents, maintain a very informative page about scams to raise awareness.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
Remove Fraudulent Content:
If the scam involves a compromised website, contact the owner to remove the fraudulent content and secure the site.
Contact the hosting company of any cybersquatted domain to take down the fraudulent page.
Reach out to the email hosting company to shut down the fraudulent account, providing a copy of the fraudulent email.
Contact social media platforms to take down fraudulent accounts.
Persistent Follow-Up:
Follow up regularly if no action is taken, and involve local CERTs if necessary to expedite the takedown process.
5. Recovery: : Objective: Restore the system to normal operations.
Assess End of the Case:
Ensure the fraudulent email address has been shut down.
Continue monitoring any associated fraudulent websites.
Remove the warning page from your website once the scam campaign ends.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Report:
Write a comprehensive crisis report, covering:
Initial cause of the incident.
Actions and timelines of important events.
What went right and what went wrong.
Incident cost.
Indicators of compromise.
Capitalize:
Reflect on what preparation steps could have improved the response.
Update contact lists with notes on the most effective ways to contact each party.
Strengthen relationships inside and outside the organization to aid in future incidents.
Improve DKIM, SPF, and DMARC filters.
Collaborate with legal teams if legal action is required.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
