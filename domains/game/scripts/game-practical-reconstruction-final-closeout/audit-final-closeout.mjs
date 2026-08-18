#!/usr/bin/env node
import fs from 'node:fs';
const s=JSON.parse(fs.readFileSync(process.argv[2]??'evidence/game-practical-reconstruction-final-closeout/final-closeout-state.json','utf8'));
const checks={
  phaseClosed:s.phaseStatus==='CLOSED',
  substrateFive:s.frozenSubstrate.length===5,
  eightCompleted:s.completedPracticalRounds.length===8,
  nextGprUnknown:s.nextGpr==='UNKNOWN',
  nextRouteUnknown:s.nextPracticalRoute==='UNKNOWN',
  nextFoundationUnknown:s.nextFoundation==='UNKNOWN',
  noGpr8:s.gpr8Admitted===false,
  noWholeGameClaim:s.wholeGameComplete===false,
  noWholePracticalClaim:s.wholePracticalSpaceComplete===false,
  strongLocalClosure:s.strongLocalClosure===true,
  sevenPracticalClusters:s.deeplyExploredPracticalClusters.length===7,
  partialMap:s.partialOrConsumerConditional.length>=6,
  ownerMap:Object.keys(s.ownedElsewhere).length>=6,
  residualHints:s.knownNonPrioritizedUnexploredHints.length>=11,
  unknownUnknownsOpen:s.unknownUnknownsOpen===true,
  protocolFreshSearch:s.requiredFutureProtocol.includes('fresh whole-Game'),
  protocolNonPrioritized:s.requiredFutureProtocol.includes('non-prioritized hints'),
  mapFirst:s.finalLaw.includes('Map first; select later')
};
if(Object.values(checks).some(v=>!v)) throw new Error(JSON.stringify(checks,null,2));
console.log(JSON.stringify({schemaVersion:1,kind:'ordivon.game.practical-reconstruction-final-closeout-audit',checkCount:Object.keys(checks).length,checks,decision:'GPR0-GPR7 practical reconstruction phase is closed with strong local closure only. No GPR8, practical route or foundation route is admitted. Future continuation must begin from a fresh unprejudiced coverage search.'},null,2));
