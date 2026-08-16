import type {
  CasefilePersonBehavior,
  CasefilePersonDefinition,
  CasefilePersonId,
  CasefileScenarioDefinition,
} from "./model.ts";

const PEOPLE: CasefilePersonDefinition[] = [
  { personId: "mira", name: "Mira Voss", role: "Archive technician" },
  { personId: "sol", name: "Sol Renn", role: "Lab systems engineer" },
  { personId: "ivo", name: "Ivo Marr", role: "Dock mechanic" },
  { personId: "nera", name: "Nera Quill", role: "Galley steward" },
];

function person(
  initialStatement: string,
  repeatStatement: string,
  confrontStatements: Record<string, string>,
): CasefilePersonBehavior {
  return { initialStatement, repeatStatement, confrontStatements };
}

const RELAY_SABOTAGE: CasefileScenarioDefinition = {
  scenarioId: "relay-sabotage",
  title: "The Silent Relay",
  hook: "A navigation relay was sabotaged minutes before departure.",
  setup: "The ship departs after eight investigation moves. Four crew members had plausible access. Build a case from traces and testimony, then commit one accusation.",
  culpritId: "sol",
  motive: "Sol disabled the relay to delay departure long enough to copy embargoed lab results from the outbound cache.",
  reconstruction: "At 21:05 Sol left the Lab with shared coolant gloves, crossed the relay corridor, disabled the relay at 21:10, then returned by the service passage and initially denied entering the corridor.",
  people: PEOPLE,
  traces: [
    { traceId: "archive-badge", label: "Archive badge history", location: "Archive", subjectId: "mira", clue: "Mira crossed the relay corridor at 20:52, but her Archive terminal was active again from 21:02 through 21:18." },
    { traceId: "coolant-fiber", label: "Coolant glove fiber", location: "Relay housing", subjectId: "sol", clue: "The fiber matches Lab glove stock issued on Sol's shift. The rack is shared, so the fiber alone does not identify who wore the glove." },
    { traceId: "dock-ratchet", label: "Ratchet scoring", location: "Relay fastener", subjectId: "ivo", clue: "The scoring matches a Dock ratchet signed out by Ivo, but the tool rack is communal after sign-out." },
    { traceId: "galley-reflection", label: "Camera reflection", location: "Galley junction", subjectId: "nera", clue: "A reflection places Nera near the junction at 21:07, but the relay corridor itself is outside frame." },
  ],
  behavior: {
    mira: person(
      "I crossed the corridor before nine. After that I was indexing cargo manifests in Archive.",
      "The Archive terminal keeps my edits. Check its activity window if you think I slipped away again.",
      { "archive-badge": "Yes, that's my badge. The time is before the sabotage, and my terminal activity resumes continuously before 21:10." },
    ),
    sol: person(
      "I stayed in the Lab after calibration. I never entered the relay corridor tonight.",
      "I already told you: Lab, calibration, then shutdown. Someone is using my shift to make this look convenient.",
      { "coolant-fiber": "The glove rack is shared. Fine—I did cross the corridor after hearing the pre-departure alarm, but I never touched the relay." },
    ),
    ivo: person(
      "I signed out the ratchet before dinner and left it on the Dock board when the seal inspection ended.",
      "Ask anyone on Dock: tools change hands after sign-out. I was under the port lift when the relay died.",
      { "dock-ratchet": "That's the ratchet number I signed out. It was back on the communal board before 20:40; the scoring cannot tell you who picked it up later." },
    ),
    nera: person(
      "I carried tea through the junction before departure checks. I never entered the relay corridor.",
      "The galley camera should show the tray. I had no reason to go near navigation equipment.",
      { "galley-reflection": "That's me with the tray. The reflection catches the junction, not the relay door; I returned to Galley immediately after." },
    ),
  },
};

const MED_CACHE: CasefileScenarioDefinition = {
  scenarioId: "missing-med-cache",
  title: "The Missing Cache",
  hook: "A sealed emergency medicine cache vanished before a quarantine transfer.",
  setup: "Eight investigation moves remain before quarantine locks the deck. Determine who diverted the cache and why, then commit one accusation.",
  culpritId: "nera",
  motive: "Nera diverted the cache to a hidden civilian compartment after learning official allocation would exclude an undocumented passenger.",
  reconstruction: "Nera borrowed Mira's archive trolley, crossed Stores during the camera reset, moved the cache through Galley service access, and hid it for an undocumented passenger before returning the trolley.",
  people: PEOPLE,
  traces: [
    { traceId: "archive-trolley", label: "Archive trolley seal", location: "Stores", subjectId: "mira", clue: "Mira's trolley seal was broken, but Archive inventory shows the trolley itself absent for fourteen minutes while Mira remained logged into catalog review." },
    { traceId: "lab-sedative", label: "Sedative residue", location: "Cache shelf", subjectId: "sol", clue: "Lab sedative residue is present on the shelf, but the compound is also stored in the missing cache." },
    { traceId: "dock-lift", label: "Dock lift record", location: "Freight lift", subjectId: "ivo", clue: "Ivo used the freight lift twice, both trips ending before the cache seal was last verified intact." },
    { traceId: "galley-thread", label: "Galley service thread", location: "Service hatch", subjectId: "nera", clue: "A thread from Nera's service apron is caught in the hatch behind Stores. The hatch bypasses the quarantine corridor cameras." },
  ],
  behavior: {
    mira: person(
      "I was in Archive reviewing transfer manifests. I didn't notice the trolley was gone until Security asked for it.",
      "My terminal edits are continuous. Someone could take the trolley without needing my badge.",
      { "archive-trolley": "The broken seal is mine, but the catalog log keeps me in Archive. I left the trolley in the public alcove after lunch." },
    ),
    sol: person(
      "I checked the cache temperature in the afternoon, not during the disappearance window.",
      "That residue is ordinary stock. The cache itself contains the same sedative compound.",
      { "lab-sedative": "The residue proves the cache or its contents touched that shelf. It does not place me there during the missing fourteen minutes." },
    ),
    ivo: person(
      "I ran lift diagnostics before quarantine. Both trips are in the controller log.",
      "The lift was parked and locked when the cache was last verified. I never opened Stores after that.",
      { "dock-lift": "Those are my diagnostics. Look at the timestamps: both finish before the cache is last recorded present." },
    ),
    nera: person(
      "I was preparing quarantine meals in Galley. I didn't enter Stores.",
      "I know what people will say because I argued about the allocation list. Arguing isn't stealing medicine.",
      { "galley-thread": "The service hatch catches apron threads all the time. ...Yes, I used it tonight. I was checking on someone the manifest pretends isn't aboard." },
    ),
  },
};

const PRESSURE_ALARM: CasefileScenarioDefinition = {
  scenarioId: "false-pressure-alarm",
  title: "Pressure Without a Leak",
  hook: "A false pressure alarm forced an evacuation and erased twenty minutes of dock work.",
  setup: "Eight investigation moves remain before the shift disperses. Find who falsified the sensor path, then commit one accusation.",
  culpritId: "ivo",
  motive: "Ivo triggered the evacuation to hide damage he caused to an unauthorized cargo clamp before the supervisor inspection.",
  reconstruction: "Ivo damaged a cargo clamp, used a maintenance bridge to inject a false pressure reading, evacuated the dock, replaced the clamp under cover of the alarm, and then returned the bridge lead to the tool wall.",
  people: PEOPLE,
  traces: [
    { traceId: "archive-print", label: "Emergency procedure print", location: "Archive printer", subjectId: "mira", clue: "Mira printed pressure procedures at 18:10 for a scheduled drill; the false alarm occurred more than two hours later." },
    { traceId: "lab-calibrator", label: "Sensor calibrator checksum", location: "Lab", subjectId: "sol", clue: "Sol's calibrator touched the pressure network that day, but its signed checksum matches the approved morning calibration." },
    { traceId: "bridge-lead", label: "Maintenance bridge lead", location: "Dock tool wall", subjectId: "ivo", clue: "A bridge lead assigned to Ivo carries fresh connector wear matching the pressure controller's service port." },
    { traceId: "galley-call", label: "Galley call timestamp", location: "Crew channel", subjectId: "nera", clue: "Nera called Dock about a meal delivery thirty seconds before the alarm; the call record keeps her on the public channel through evacuation." },
  ],
  behavior: {
    mira: person(
      "I printed the procedure for the drill and went back to Archive. The real alarm was hours later.",
      "The print queue and Archive desk camera both keep the drill work separate from tonight's alarm.",
      { "archive-print": "That's my print job. The timestamp is 18:10; if someone used it later, the paper was sitting in the common procedure rack." },
    ),
    sol: person(
      "I calibrated the sensors in the morning under the approved maintenance ticket.",
      "The calibrator signs every write. If I changed the network tonight, its checksum would not match the morning ticket.",
      { "lab-calibrator": "The checksum is exactly why this isn't evidence against me. It records the authorized morning calibration, not the false alarm." },
    ),
    ivo: person(
      "I evacuated with everyone else. I didn't touch the pressure controller before the alarm.",
      "Dock tools get dirty. Fresh wear doesn't mean I used that lead on the controller tonight.",
      { "bridge-lead": "That lead is assigned to my wall slot. I used it on a cargo clamp controller earlier—...not the pressure controller. The service-port match could be from old work." },
    ),
    nera: person(
      "I was on the crew channel arranging Dock meals when the alarm cut us off.",
      "The call log should still have the whole exchange. I never left Galley service during the evacuation start.",
      { "galley-call": "That's my call. You can hear me still talking when the pressure alarm begins in the background." },
    ),
  },
};

export const CASEFILE_SCENARIOS: CasefileScenarioDefinition[] = [RELAY_SABOTAGE, MED_CACHE, PRESSURE_ALARM];
export const DEFAULT_CASEFILE_SCENARIO_ID = RELAY_SABOTAGE.scenarioId;

export function casefileScenario(scenarioId: string): CasefileScenarioDefinition {
  const scenario = CASEFILE_SCENARIOS.find((entry) => entry.scenarioId === scenarioId);
  if (!scenario) throw new TypeError(`unknown Casefile scenario: ${scenarioId}`);
  return scenario;
}

export function casefilePersonName(scenario: CasefileScenarioDefinition, personId: CasefilePersonId): string {
  const person = scenario.people.find((entry) => entry.personId === personId);
  if (!person) throw new TypeError(`unknown Casefile person: ${personId}`);
  return person.name;
}
