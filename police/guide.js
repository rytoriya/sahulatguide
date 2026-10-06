/*
 * "How police stations work" section of the Police Station Directory.
 * Shown under every district (before the site footer), with the district and province filled in.
 * Edit the text here; keep each fact backed by a source in SOURCES.
 */
(function () {
  "use strict";

  // Complaint routes and services that differ by province.
  var PROV = {
    pb: {
      complain: [
        ["IGP Police Complaint Centre: <b>1787</b>", "Call or SMS 1787 (it replaced 8787). It takes complaints about an FIR not being registered, illegal detention, arrest of innocent people, false FIRs, slack investigation and bribe demands. An officer of at least SDPO rank must contact you within 8 hours."],
        ["District police office", "Every district has a District Police Officer (in Lahore, Rawalpindi, Faisalabad, Gujranwala and Multan, a City Police Officer). You can meet the DPO or SP during open-court hours."],
      ],
      services: "Punjab Police run front desks at police stations and Police Khidmat Markaz service centres in districts for character certificates, vehicle verification, tenant and employee registration and reports of lost documents.",
    },
    sd: {
      complain: [
        ["IGP complaint helpline: <b>9110</b>", "The Sindh Police complaint management system at the Central Police Office, Karachi, takes complaints by phone, SMS and online."],
        ["CPLC (Citizens-Police Liaison Committee)", "In Karachi, CPLC reporting cells sit in the district SSP offices. They help with FIRs, kidnapping, vehicle theft and tracing cases."],
      ],
      services: "Each district is headed by a Senior Superintendent of Police (SSP). In Karachi, districts are grouped into zones under a DIG.",
    },
    kp: {
      complain: [
        ["Police Access Service (PAS)", "Complain by SMS, online, phone, post or in person at any District Police Office or the Central Police Office, Peshawar. You get a complaint code by SMS, and the officer concerned must contact you within 24 hours."],
        ["Dispute Resolution Councils (DRCs)", "Respected local members (lawyers, retired officers, teachers) settle minor disputes without going to court, and can also review contested police investigations."],
      ],
      services: "Khyber Pakhtunkhwa police stations have front desks for complaints and many districts have women's help desks.",
    },
    ict: {
      complain: [
        ["Pukaar-15: <b>15</b>", "Call 15 in any emergency. The nearest Eagle Squad comes first, and the police station's staff can register the FIR on the spot."],
        ["ICT-15 app", "The Islamabad Police app lets you alert the police without calling."],
      ],
      services: "Islamabad is covered by the Safe City camera network, linked to the police command and control centre.",
    },
    bl: {
      complain: [
        ["Police emergency: <b>15</b>", "Available 24 hours across Balochistan for any threat, emergency or crime."],
        ["Balochistan Women Helpline: <b>1089</b>", "For harassment at home or work, domestic violence and property issues faced by women."],
      ],
      services: "Each district has a District Police Officer; contact the district police office for station details.",
    },
    ajk: {
      complain: [["Police emergency: <b>15</b>", "Available 24 hours. For complaints, contact the district police office or the Central Police Office, Muzaffarabad."]],
      services: "Azad Jammu & Kashmir Police cover the territory's 10 districts from the Central Police Office in Muzaffarabad.",
    },
    gb: {
      complain: [["Police emergency: <b>15</b>", "Available 24 hours. For complaints, contact the district police office or the Central Police Office, Gilgit."]],
      services: "Gilgit-Baltistan Police run about 65 police stations and have opened Police Khidmat Markaz service centres.",
    },
  };

  var SOURCES = [
    ["Punjab Police: IGP Police Complaint Centre", "https://rposwl.punjabpolice.gov.pk/node/828"],
    ["Lahore Police: complaints mechanism", "https://lahorepolice.punjab.gov.pk/index.php/complaints-mechanism"],
    ["Sindh High Court judgments on FIRs and the Justice of Peace", "https://caselaw.shc.gov.pk/"],
    ["Islamabad Police: emergency 15", "https://islamabadpolice.gov.pk/r15.php"],
    ["CPLC Karachi", "https://www.cplc.org.pk/"],
    ["Gilgit-Baltistan Police", "https://gbp.gov.pk/"],
  ];

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  window.policeGuide = function (d) {
    var p = PROV[d.prov.id] || PROV.ajk;
    var place = esc(d.name);
    return '' +
      '<h2>How police stations work in ' + place + '</h2>' +
      '<p class="lead">A police station (thana) is where you report a crime, register an FIR and ask the police for help. Each station covers a fixed area of ' + place + ' District. If you are not sure which station covers the place where something happened, call <a href="tel:15">15</a>: the operator sends the nearest police.</p>' +
      '<div class="gcols">' +
        '<div class="gbox"><h3>Who runs the station</h3><ul>' +
          '<li>The <b>Station House Officer (SHO)</b>, usually an Inspector or Sub-Inspector, is in charge of a police station.</li>' +
          '<li>A <b>duty officer</b> (moharrar) receives people, records reports in the daily diary (roznamcha) and writes FIRs.</li>' +
          '<li>Several stations form a <b>circle</b> or sub-division under a <b>Sub-Divisional Police Officer (SDPO)</b>, a DSP or ASP.</li>' +
          '<li>The district is headed by a <b>District Police Officer</b> (an SSP or a City Police Officer in large cities).</li>' +
        '</ul></div>' +
        '<div class="gbox"><h3>Registering an FIR</h3><ul>' +
          '<li>An <b>FIR</b> (First Information Report) starts a criminal case. Under <b>section 154</b> of the Code of Criminal Procedure, the officer in charge must register information about a cognizable offence such as theft, robbery, assault, harassment or fraud.</li>' +
          '<li>Tell the duty officer what happened or give a written application. Read the FIR before you sign it.</li>' +
          '<li>Your <b>copy of the FIR is free</b>. Nobody may charge a fee for registering it.</li>' +
          '<li>For minor, non-cognizable matters and lost documents, the police record a report in the daily diary instead.</li>' +
          '<li>If the police refuse, complain to the SDPO or the district police office, use the complaint line below, or apply to the <b>Justice of Peace</b> (the Sessions or Additional Sessions Judge) under <b>section 22-A</b> of the CrPC, who can order the police to register it.</li>' +
        '</ul></div>' +
        '<div class="gbox"><h3>Services and facilities</h3><ul>' +
          '<li><b>Front desk:</b> complaints are logged and you are given a reference number to follow up.</li>' +
          '<li><b>Women and children:</b> many districts have a women\'s help desk or a women police station; you can ask for a female officer.</li>' +
          '<li><b>Reports for lost items and documents</b> (often needed for a duplicate CNIC, passport or bank card).</li>' +
          '<li><b>Certificates and verification:</b> police character certificates, tenant and domestic-worker registration and vehicle verification, through police service centres.</li>' +
          '<li>' + esc(p.services) + '</li>' +
        '</ul></div>' +
        '<div class="gbox"><h3>Your rights</h3><ul>' +
          '<li>If you are arrested, you must be told why and produced before a magistrate within <b>24 hours</b> (Article 10 of the Constitution; section 61 CrPC).</li>' +
          '<li>You may consult and be defended by a <b>lawyer</b> of your choice (Article 10).</li>' +
          '<li>A woman may only be searched by another <b>woman</b> (section 52 CrPC).</li>' +
          '<li>Keep a note of the officer\'s name, the date and any reference or FIR number.</li>' +
        '</ul></div>' +
      '</div>' +
      '<h3 class="gsub">Complaints and help in ' + esc(d.prov.name) + '</h3>' +
      '<div class="gcomp">' + p.complain.map(function (c) { return '<div class="gitem"><div class="gt">' + c[0] + '</div><p>' + esc(c[1]) + '</p></div>'; }).join("") + '</div>' +
      '<p class="gsrc">Sources: ' + SOURCES.map(function (s) { return '<a href="' + s[1] + '" target="_blank" rel="nofollow noopener">' + esc(s[0]) + '</a>'; }).join(" · ") + '. Laws: Code of Criminal Procedure 1898 (sections 52, 61, 154, 22-A) and the Constitution of Pakistan (Article 10). This is general information, not legal advice.</p>';
  };
})();
