# Intergrate the event types from m2e2, rams, and wikievents into a unified set of event types with descriptions and original type mappings

new_event_types_groups  = {'conflict': [('Conflict:Attack', 'm2e2'),
  ('Conflict:Demonstrate', 'm2e2'),
  ('conflict.attack.airstrikemissilestrike', 'rams'),
  ('conflict.attack.biologicalchemicalpoisonattack', 'rams'),
  ('conflict.attack.bombing', 'rams'),
  ('conflict.attack.firearmattack', 'rams'),
  ('conflict.attack.hanging', 'rams'),
  ('conflict.attack.invade', 'rams'),
  ('conflict.attack.n/a', 'rams'),
  ('conflict.attack.selfdirectedbattle', 'rams'),
  ('conflict.attack.setfire', 'rams'),
  ('conflict.attack.stabbing', 'rams'),
  ('conflict.attack.stealrobhijack', 'rams'),
  ('conflict.attack.strangling', 'rams'),
  ('conflict.demonstrate.marchprotestpoliticalgathering', 'rams'),
  ('conflict.demonstrate.n/a', 'rams'),
  ('conflict.yield.n/a', 'rams'),
  ('conflict.yield.retreat', 'rams'),
  ('conflict.yield.surrender', 'rams'),
  ('Conflict.Attack.DetonateExplode', 'wikievents'),
  ('Conflict.Attack.Unspecified', 'wikievents'),
  ('Conflict.Defeat.Unspecified', 'wikievents'),
  ('Conflict.Demonstrate.DemonstrateWithViolence', 'wikievents'),
  ('Conflict.Demonstrate.Unspecified', 'wikievents')],
 'contact': [('Contact:Meet', 'm2e2'),
  ('Contact:Phone-Write', 'm2e2'),
  ('contact.collaborate.correspondence', 'rams'),
  ('contact.collaborate.meet', 'rams'),
  ('contact.collaborate.n/a', 'rams'),
  ('contact.commandorder.broadcast', 'rams'),
  ('contact.commandorder.correspondence', 'rams'),
  ('contact.commandorder.meet', 'rams'),
  ('contact.commandorder.n/a', 'rams'),
  ('contact.commitmentpromiseexpressintent.broadcast', 'rams'),
  ('contact.commitmentpromiseexpressintent.correspondence', 'rams'),
  ('contact.commitmentpromiseexpressintent.meet', 'rams'),
  ('contact.commitmentpromiseexpressintent.n/a', 'rams'),
  ('contact.discussion.correspondence', 'rams'),
  ('contact.discussion.meet', 'rams'),
  ('contact.discussion.n/a', 'rams'),
  ('contact.funeralvigil.meet', 'rams'),
  ('contact.funeralvigil.n/a', 'rams'),
  ('contact.mediastatement.broadcast', 'rams'),
  ('contact.mediastatement.n/a', 'rams'),
  ('contact.negotiate.correspondence', 'rams'),
  ('contact.negotiate.meet', 'rams'),
  ('contact.negotiate.n/a', 'rams'),
  ('contact.prevarication.broadcast', 'rams'),
  ('contact.prevarication.correspondence', 'rams'),
  ('contact.prevarication.meet', 'rams'),
  ('contact.prevarication.n/a', 'rams'),
  ('contact.publicstatementinperson.broadcast', 'rams'),
  ('contact.publicstatementinperson.n/a', 'rams'),
  ('contact.requestadvise.broadcast', 'rams'),
  ('contact.requestadvise.correspondence', 'rams'),
  ('contact.requestadvise.meet', 'rams'),
  ('contact.requestadvise.n/a', 'rams'),
  ('contact.threatencoerce.broadcast', 'rams'),
  ('contact.threatencoerce.correspondence', 'rams'),
  ('contact.threatencoerce.meet', 'rams'),
  ('contact.threatencoerce.n/a', 'rams'),
  ('Contact.Contact.Broadcast', 'wikievents'),
  ('Contact.Contact.Correspondence', 'wikievents'),
  ('Contact.Contact.Meet', 'wikievents'),
  ('Contact.Contact.Unspecified', 'wikievents'),
  ('Contact.RequestCommand.Broadcast', 'wikievents'),
  ('Contact.RequestCommand.Correspondence', 'wikievents'),
  ('Contact.RequestCommand.Meet', 'wikievents'),
  ('Contact.RequestCommand.Unspecified', 'wikievents'),
  ('Contact.ThreatenCoerce.Broadcast', 'wikievents'),
  ('Contact.ThreatenCoerce.Correspondence', 'wikievents'),
  ('Contact.ThreatenCoerce.Unspecified', 'wikievents')],
 'justice': [('Justice:Arrest-Jail', 'm2e2'),
  ('justice.arrestjaildetain.arrestjaildetain', 'rams'),
  ('justice.initiatejudicialprocess.chargeindict', 'rams'),
  ('justice.initiatejudicialprocess.n/a', 'rams'),
  ('justice.initiatejudicialprocess.trialhearing', 'rams'),
  ('justice.investigate.investigatecrime', 'rams'),
  ('justice.investigate.n/a', 'rams'),
  ('justice.judicialconsequences.convict', 'rams'),
  ('justice.judicialconsequences.execute', 'rams'),
  ('justice.judicialconsequences.extradite', 'rams'),
  ('justice.judicialconsequences.n/a', 'rams'),
  ('Justice.Acquit.Unspecified', 'wikievents'),
  ('Justice.ArrestJailDetain.Unspecified', 'wikievents'),
  ('Justice.ChargeIndict.Unspecified', 'wikievents'),
  ('Justice.Convict.Unspecified', 'wikievents'),
  ('Justice.InvestigateCrime.Unspecified', 'wikievents'),
  ('Justice.ReleaseParole.Unspecified', 'wikievents'),
  ('Justice.Sentence.Unspecified', 'wikievents'),
  ('Justice.TrialHearing.Unspecified', 'wikievents')],
 'life': [('Life:Die', 'm2e2'),
  ('life.die.deathcausedbyviolentevents', 'rams'),
  ('life.die.n/a', 'rams'),
  ('life.die.nonviolentdeath', 'rams'),
  ('life.injure.illnessdegradationhungerthirst', 'rams'),
  ('life.injure.illnessdegradationphysical', 'rams'),
  ('life.injure.injurycausedbyviolentevents', 'rams'),
  ('life.injure.n/a', 'rams'),
  ('Life.Die.Unspecified', 'wikievents'),
  ('Life.Infect.Unspecified', 'wikievents'),
  ('Life.Injure.Unspecified', 'wikievents')],
 'movement': [('Movement:Transport', 'm2e2'),
  ('movement.transportartifact.bringcarryunload', 'rams'),
  ('movement.transportartifact.disperseseparate', 'rams'),
  ('movement.transportartifact.fall', 'rams'),
  ('movement.transportartifact.grantentry', 'rams'),
  ('movement.transportartifact.hide', 'rams'),
  ('movement.transportartifact.n/a', 'rams'),
  ('movement.transportartifact.nonviolentthrowlaunch', 'rams'),
  ('movement.transportartifact.prevententry', 'rams'),
  ('movement.transportartifact.preventexit', 'rams'),
  ('movement.transportartifact.receiveimport', 'rams'),
  ('movement.transportartifact.sendsupplyexport', 'rams'),
  ('movement.transportartifact.smuggleextract', 'rams'),
  ('movement.transportperson.bringcarryunload', 'rams'),
  ('movement.transportperson.disperseseparate', 'rams'),
  ('movement.transportperson.evacuationrescue', 'rams'),
  ('movement.transportperson.fall', 'rams'),
  ('movement.transportperson.grantentryasylum', 'rams'),
  ('movement.transportperson.hide', 'rams'),
  ('movement.transportperson.n/a', 'rams'),
  ('movement.transportperson.prevententry', 'rams'),
  ('movement.transportperson.preventexit', 'rams'),
  ('movement.transportperson.selfmotion', 'rams'),
  ('movement.transportperson.smuggleextract', 'rams'),
  ('Movement.Transportation.Evacuation', 'wikievents'),
  ('Movement.Transportation.IllegalTransportation', 'wikievents'),
  ('Movement.Transportation.PreventPassage', 'wikievents'),
  ('Movement.Transportation.Unspecified', 'wikievents')],
 'transaction': [('Transaction:Transfer-Money', 'm2e2'),
  ('transaction.transaction.embargosanction', 'rams'),
  ('transaction.transaction.giftgrantprovideaid', 'rams'),
  ('transaction.transaction.n/a', 'rams'),
  ('transaction.transaction.transfercontrol', 'rams'),
  ('transaction.transfermoney.borrowlend', 'rams'),
  ('transaction.transfermoney.embargosanction', 'rams'),
  ('transaction.transfermoney.giftgrantprovideaid', 'rams'),
  ('transaction.transfermoney.n/a', 'rams'),
  ('transaction.transfermoney.payforservice', 'rams'),
  ('transaction.transfermoney.purchase', 'rams'),
  ('transaction.transferownership.borrowlend', 'rams'),
  ('transaction.transferownership.embargosanction', 'rams'),
  ('transaction.transferownership.giftgrantprovideaid', 'rams'),
  ('transaction.transferownership.n/a', 'rams'),
  ('transaction.transferownership.purchase', 'rams'),
  ('Transaction.Donation.Unspecified', 'wikievents'),
  ('Transaction.ExchangeBuySell.Unspecified', 'wikievents')],
 'artifactexistence': [('artifactexistence.damagedestroy.damage', 'rams'),
  ('artifactexistence.damagedestroy.destroy', 'rams'),
  ('artifactexistence.damagedestroy.n/a', 'rams'),
  ('ArtifactExistence.DamageDestroyDisableDismantle.Damage', 'wikievents'),
  ('ArtifactExistence.DamageDestroyDisableDismantle.Destroy', 'wikievents'),
  ('ArtifactExistence.DamageDestroyDisableDismantle.DisableDefuse',
   'wikievents'),
  ('ArtifactExistence.DamageDestroyDisableDismantle.Dismantle', 'wikievents'),
  ('ArtifactExistence.DamageDestroyDisableDismantle.Unspecified',
   'wikievents'),
  ('ArtifactExistence.ManufactureAssemble.Unspecified', 'wikievents')],
 'disaster': [('disaster.accidentcrash.accidentcrash', 'rams'),
  ('disaster.fireexplosion.fireexplosion', 'rams'),
  ('Disaster.Crash.Unspecified', 'wikievents'),
  ('Disaster.DiseaseOutbreak.Unspecified', 'wikievents')],
 'government': [('government.agreements.acceptagreementcontractceasefire',
   'rams'),
  ('government.agreements.n/a', 'rams'),
  ('government.agreements.rejectnullifyagreementcontractceasefire', 'rams'),
  ('government.agreements.violateagreement', 'rams'),
  ('government.formation.mergegpe', 'rams'),
  ('government.formation.n/a', 'rams'),
  ('government.formation.startgpe', 'rams'),
  ('government.legislate.legislate', 'rams'),
  ('government.spy.spy', 'rams'),
  ('government.vote.castvote', 'rams'),
  ('government.vote.n/a', 'rams'),
  ('government.vote.violationspreventvote', 'rams')],
 'inspection': [('inspection.sensoryobserve.inspectpeopleorganization',
   'rams'),
  ('inspection.sensoryobserve.monitorelection', 'rams'),
  ('inspection.sensoryobserve.n/a', 'rams'),
  ('inspection.sensoryobserve.physicalinvestigateinspect', 'rams')],
 'manufacture': [('manufacture.artifact.build', 'rams'),
  ('manufacture.artifact.createintellectualproperty', 'rams'),
  ('manufacture.artifact.createmanufacture', 'rams'),
  ('manufacture.artifact.n/a', 'rams')],
 'personnel': [('personnel.elect.n/a', 'rams'),
  ('personnel.elect.winelection', 'rams'),
  ('personnel.endposition.firinglayoff', 'rams'),
  ('personnel.endposition.n/a', 'rams'),
  ('personnel.endposition.quitretire', 'rams'),
  ('personnel.startposition.hiring', 'rams'),
  ('personnel.startposition.n/a', 'rams'),
  ('Personnel.EndPosition.Unspecified', 'wikievents'),
  ('Personnel.StartPosition.Unspecified', 'wikievents')],
 'cognitive': [('Cognitive.IdentifyCategorize.Unspecified', 'wikievents'),
  ('Cognitive.Inspection.SensoryObserve', 'wikievents'),
  ('Cognitive.Research.Unspecified', 'wikievents'),
  ('Cognitive.TeachingTrainingLearning.Unspecified', 'wikievents')],
 'control': [('Control.ImpedeInterfereWith.Unspecified', 'wikievents')],
 'genericcrime': [('GenericCrime.GenericCrime.GenericCrime', 'wikievents')],
 'medical': [('Medical.Intervention.Unspecified', 'wikievents')]}

new_event_types_with_description = {
  "conflict_Attack": {
    "parent_group": "conflict",
    "secondary_type": "Attack",
    "description": "An event involving intentional violent action against a target, including physical assaults, armed attacks, invasions, or destructive force.",
    "original_event_types": [
      ["Conflict:Attack","m2e2"],
      ["conflict.attack.airstrikemissilestrike","rams"],
      ["conflict.attack.biologicalchemicalpoisonattack","rams"],
      ["conflict.attack.bombing","rams"],
      ["conflict.attack.firearmattack","rams"],
      ["conflict.attack.hanging","rams"],
      ["conflict.attack.invade","rams"],
      ["conflict.attack.n/a","rams"],
      ["conflict.attack.selfdirectedbattle","rams"],
      ["conflict.attack.setfire","rams"],
      ["conflict.attack.stabbing","rams"],
      ["conflict.attack.stealrobhijack","rams"],
      ["conflict.attack.strangling","rams"],
      ["Conflict.Attack.DetonateExplode","wikievents"],
      ["Conflict.Attack.Unspecified","wikievents"]
    ]
  },
  "conflict_Demonstrate": {
    "parent_group": "conflict",
    "secondary_type": "Demonstrate",
    "description": "An event where individuals or groups publicly gather to protest, march, or demonstrate, sometimes involving unrest or violence.",
    "original_event_types": [
      ["Conflict:Demonstrate","m2e2"],
      ["conflict.demonstrate.marchprotestpoliticalgathering","rams"],
      ["conflict.demonstrate.n/a","rams"],
      ["Conflict.Demonstrate.DemonstrateWithViolence","wikievents"],
      ["Conflict.Demonstrate.Unspecified","wikievents"]
    ]
  },
  "conflict_Yield": {
    "parent_group": "conflict",
    "secondary_type": "Yield",
    "description": "An event in which a party retreats, surrenders, or otherwise concedes defeat during a conflict.",
    "original_event_types": [
      ["conflict.yield.n/a","rams"],
      ["conflict.yield.retreat","rams"],
      ["conflict.yield.surrender","rams"],
      ["Conflict.Defeat.Unspecified","wikievents"]
    ]
  },

  "contact_Meet_Correspond": {
    "parent_group": "contact",
    "secondary_type": "Meet/Correspond",
    "description": "An event where parties communicate directly through meetings, discussions, negotiations, collaboration, or correspondence.",
    "original_event_types": [
      ["Contact:Meet","m2e2"],
      ["Contact:Phone-Write","m2e2"],
      ["contact.collaborate.correspondence","rams"],
      ["contact.collaborate.meet","rams"],
      ["contact.collaborate.n/a","rams"],
      ["contact.negotiate.correspondence","rams"],
      ["contact.negotiate.meet","rams"],
      ["contact.negotiate.n/a","rams"],
      ["contact.discussion.correspondence","rams"],
      ["contact.discussion.meet","rams"],
      ["contact.discussion.n/a","rams"],
      ["contact.funeralvigil.meet","rams"],
      ["contact.funeralvigil.n/a","rams"]
    ]
  },
  "contact_Broadcast_Public_Statement": {
    "parent_group": "contact",
    "secondary_type": "Broadcast/Public Statement",
    "description": "An event involving public communication delivered via broadcast media or in-person public statements.",
    "original_event_types": [
      ["contact.mediastatement.broadcast","rams"],
      ["contact.mediastatement.n/a","rams"],
      ["contact.publicstatementinperson.broadcast","rams"],
      ["contact.publicstatementinperson.n/a","rams"]
    ]
  },
  "contact_Command_Order_Request": {
    "parent_group": "contact",
    "secondary_type": "Command/Order/Request",
    "description": "An event where one party issues a command, makes a formal request, or expresses intent or commitment toward another party.",
    "original_event_types": [
      ["contact.commandorder.broadcast","rams"],
      ["contact.commandorder.correspondence","rams"],
      ["contact.commandorder.meet","rams"],
      ["contact.commandorder.n/a","rams"],
      ["contact.commitmentpromiseexpressintent.broadcast","rams"],
      ["contact.commitmentpromiseexpressintent.correspondence","rams"],
      ["contact.commitmentpromiseexpressintent.meet","rams"],
      ["contact.commitmentpromiseexpressintent.n/a","rams"],
      ["contact.requestadvise.broadcast","rams"],
      ["contact.requestadvise.correspondence","rams"],
      ["contact.requestadvise.meet","rams"],
      ["contact.requestadvise.n/a","rams"],
      ["Contact.RequestCommand.Broadcast","wikievents"],
      ["Contact.RequestCommand.Correspondence","wikievents"],
      ["Contact.RequestCommand.Meet","wikievents"],
      ["Contact.RequestCommand.Unspecified","wikievents"]
    ]
  },
  "contact_Threaten_Coerce_Prevarication": {
    "parent_group": "contact",
    "secondary_type": "Threaten/Coerce/Prevarication",
    "description": "An event involving threats, coercion, deception, or evasive communication directed at another party.",
    "original_event_types": [
      ["contact.threatencoerce.broadcast","rams"],
      ["contact.threatencoerce.correspondence","rams"],
      ["contact.threatencoerce.meet","rams"],
      ["contact.threatencoerce.n/a","rams"],
      ["contact.prevarication.broadcast","rams"],
      ["contact.prevarication.correspondence","rams"],
      ["contact.prevarication.meet","rams"],
      ["contact.prevarication.n/a","rams"],
      ["Contact.ThreatenCoerce.Broadcast","wikievents"],
      ["Contact.ThreatenCoerce.Correspondence","wikievents"],
      ["Contact.ThreatenCoerce.Unspecified","wikievents"]
    ]
  },
  "contact_General_Contact": {
    "parent_group": "contact",
    "secondary_type": "General Contact",
    "description": "A general communication event that does not specify the precise mode or intent of interaction.",
    "original_event_types": [
      ["Contact.Contact.Broadcast","wikievents"],
      ["Contact.Contact.Correspondence","wikievents"],
      ["Contact.Contact.Meet","wikievents"],
      ["Contact.Contact.Unspecified","wikievents"]
    ]
  },

  "justice_Arrest_Jail_Detain": {
    "parent_group": "justice",
    "secondary_type": "Arrest/Jail/Detain",
    "description": "A legal enforcement event in which an individual is arrested, jailed, or otherwise detained by authorities.",
    "original_event_types": [
      ["Justice:Arrest-Jail","m2e2"],
      ["justice.arrestjaildetain.arrestjaildetain","rams"],
      ["Justice.ArrestJailDetain.Unspecified","wikievents"]
    ]
  },
  "justice_Initiate_Judicial_Process": {
    "parent_group": "justice",
    "secondary_type": "Initiate Judicial Process",
    "description": "An event that begins formal legal proceedings such as charging, indicting, or conducting a trial or hearing.",
    "original_event_types": [
      ["justice.initiatejudicialprocess.chargeindict","rams"],
      ["justice.initiatejudicialprocess.n/a","rams"],
      ["justice.initiatejudicialprocess.trialhearing","rams"],
      ["Justice.ChargeIndict.Unspecified","wikievents"],
      ["Justice.TrialHearing.Unspecified","wikievents"]
    ]
  },
  "justice_Investigate": {
    "parent_group": "justice",
    "secondary_type": "Investigate",
    "description": "An event involving official investigation into suspected criminal or legal wrongdoing.",
    "original_event_types": [
      ["justice.investigate.investigatecrime","rams"],
      ["justice.investigate.n/a","rams"],
      ["Justice.InvestigateCrime.Unspecified","wikievents"]
    ]
  },
  "justice_Judicial_Consequences": {
    "parent_group": "justice",
    "secondary_type": "Judicial Consequences",
    "description": "An event representing the outcome of a judicial process, including conviction, sentencing, acquittal, execution, or extradition.",
    "original_event_types": [
      ["justice.judicialconsequences.convict","rams"],
      ["justice.judicialconsequences.execute","rams"],
      ["justice.judicialconsequences.extradite","rams"],
      ["justice.judicialconsequences.n/a","rams"],
      ["Justice.Acquit.Unspecified","wikievents"],
      ["Justice.Convict.Unspecified","wikievents"],
      ["Justice.ReleaseParole.Unspecified","wikievents"],
      ["Justice.Sentence.Unspecified","wikievents"]
    ]
  },
  "life_Die_Death": {
    "parent_group": "life",
    "secondary_type": "Die/Death",
    "description": "An event in which a person dies due to violent or nonviolent causes.",
    "original_event_types": [
      ["Life:Die","m2e2"],
      ["life.die.deathcausedbyviolentevents","rams"],
      ["life.die.n/a","rams"],
      ["life.die.nonviolentdeath","rams"],
      ["Life.Die.Unspecified","wikievents"]
    ]
  },
  "life_Injure_Harm": {
    "parent_group": "life",
    "secondary_type": "Injure/Harm",
    "description": "An event where a person suffers physical injury, harm, or health degradation from violent or nonviolent causes.",
    "original_event_types": [
      ["life.injure.illnessdegradationhungerthirst","rams"],
      ["life.injure.illnessdegradationphysical","rams"],
      ["life.injure.injurycausedbyviolentevents","rams"],
      ["life.injure.n/a","rams"],
      ["Life.Injure.Unspecified","wikievents"]
    ]
  },
  "life_Infect_Disease": {
    "parent_group": "life",
    "secondary_type": "Infect/Disease",
    "description": "An event involving infection or the contraction of a disease.",
    "original_event_types": [
      ["Life.Infect.Unspecified","wikievents"]
    ]
  },

  "movement_Transport_Artifact": {
    "parent_group": "movement",
    "secondary_type": "Transport Artifact",
    "description": "An event involving the movement, transfer, hiding, smuggling, or relocation of physical objects or goods.",
    "original_event_types": [
      ["Movement:Transport","m2e2"],
      ["movement.transportartifact.bringcarryunload","rams"],
      ["movement.transportartifact.disperseseparate","rams"],
      ["movement.transportartifact.fall","rams"],
      ["movement.transportartifact.grantentry","rams"],
      ["movement.transportartifact.hide","rams"],
      ["movement.transportartifact.n/a","rams"],
      ["movement.transportartifact.nonviolentthrowlaunch","rams"],
      ["movement.transportartifact.prevententry","rams"],
      ["movement.transportartifact.preventexit","rams"],
      ["movement.transportartifact.receiveimport","rams"],
      ["movement.transportartifact.sendsupplyexport","rams"],
      ["movement.transportartifact.smuggleextract","rams"]
    ]
  },
  "movement_Transport_Person": {
    "parent_group": "movement",
    "secondary_type": "Transport Person",
    "description": "An event in which individuals are transported, evacuated, rescued, smuggled, or otherwise moved between locations.",
    "original_event_types": [
      ["movement.transportperson.bringcarryunload","rams"],
      ["movement.transportperson.disperseseparate","rams"],
      ["movement.transportperson.evacuationrescue","rams"],
      ["movement.transportperson.fall","rams"],
      ["movement.transportperson.grantentryasylum","rams"],
      ["movement.transportperson.hide","rams"],
      ["movement.transportperson.n/a","rams"],
      ["movement.transportperson.prevententry","rams"],
      ["movement.transportperson.preventexit","rams"],
      ["movement.transportperson.selfmotion","rams"],
      ["movement.transportperson.smuggleextract","rams"]
    ]
  },
  "movement_General_Transportation": {
    "parent_group": "movement",
    "secondary_type": "General Transportation",
    "description": "An event referring broadly to transportation activities, including restricted or illegal passage.",
    "original_event_types": [
      ["Movement.Transportation.Evacuation","wikievents"],
      ["Movement.Transportation.IllegalTransportation","wikievents"],
      ["Movement.Transportation.PreventPassage","wikievents"],
      ["Movement.Transportation.Unspecified","wikievents"]
    ]
  },

  "transaction_Transfer_Money": {
    "parent_group": "transaction",
    "secondary_type": "Transfer Money",
    "description": "A financial transaction event involving the exchange, lending, donation, purchase, or sanctioned transfer of money.",
    "original_event_types": [
      ["Transaction:Transfer-Money","m2e2"],
      ["transaction.transfermoney.borrowlend","rams"],
      ["transaction.transfermoney.embargosanction","rams"],
      ["transaction.transfermoney.giftgrantprovideaid","rams"],
      ["transaction.transfermoney.n/a","rams"],
      ["transaction.transfermoney.payforservice","rams"],
      ["transaction.transfermoney.purchase","rams"]
    ]
  },
  "transaction_Transfer_Ownership_Control": {
    "parent_group": "transaction",
    "secondary_type": "Transfer Ownership/Control",
    "description": "An event where ownership or control of assets, goods, or resources is transferred between parties.",
    "original_event_types": [
      ["transaction.transaction.embargosanction","rams"],
      ["transaction.transaction.giftgrantprovideaid","rams"],
      ["transaction.transaction.n/a","rams"],
      ["transaction.transaction.transfercontrol","rams"],
      ["transaction.transferownership.borrowlend","rams"],
      ["transaction.transferownership.embargosanction","rams"],
      ["transaction.transferownership.giftgrantprovideaid","rams"],
      ["transaction.transferownership.n/a","rams"],
      ["transaction.transferownership.purchase","rams"],
      ["Transaction.Donation.Unspecified","wikievents"],
      ["Transaction.ExchangeBuySell.Unspecified","wikievents"]
    ]
  },

  "artifact_existence_Damage_Destroy_Disable_Dismantle": {
    "parent_group": "artifactexistence",
    "secondary_type": "Damage/Destroy/Disable/Dismantle",
    "description": "An event involving the damaging, destruction, disabling, or dismantling of a physical object or infrastructure.",
    "original_event_types": [
      ["artifactexistence.damagedestroy.damage","rams"],
      ["artifactexistence.damagedestroy.destroy","rams"],
      ["artifactexistence.damagedestroy.n/a","rams"],
      ["ArtifactExistence.DamageDestroyDisableDismantle.Damage","wikievents"],
      ["ArtifactExistence.DamageDestroyDisableDismantle.Destroy","wikievents"],
      ["ArtifactExistence.DamageDestroyDisableDismantle.DisableDefuse","wikievents"],
      ["ArtifactExistence.DamageDestroyDisableDismantle.Dismantle","wikievents"],
      ["ArtifactExistence.DamageDestroyDisableDismantle.Unspecified","wikievents"]
    ]
  },
  "artifact_existence_Manufacture_Assemble": {
    "parent_group": "artifactexistence",
    "secondary_type": "Manufacture/Assemble",
    "description": "An event where an artifact is produced, assembled, or constructed.",
    "original_event_types": [
      ["ArtifactExistence.ManufactureAssemble.Unspecified","wikievents"]
    ]
  },

  "disaster_Accident_Crash": {
    "parent_group": "disaster",
    "secondary_type": "Accident/Crash",
    "description": "An unintentional event involving a crash or accident causing damage or harm.",
    "original_event_types": [
      ["disaster.accidentcrash.accidentcrash","rams"],
      ["Disaster.Crash.Unspecified","wikievents"]
    ]
  },
  "disaster_Fire_Explosion": {
    "parent_group": "disaster",
    "secondary_type": "Fire/Explosion",
    "description": "An event characterized by unintended fire or explosion resulting in damage or danger.",
    "original_event_types": [
      ["disaster.fireexplosion.fireexplosion","rams"]
    ]
  },
  "disaster_Disease_Outbreak": {
    "parent_group": "disaster",
    "secondary_type": "Disease Outbreak",
    "description": "An event involving the rapid spread of a disease affecting a population.",
    "original_event_types": [
      ["Disaster.DiseaseOutbreak.Unspecified","wikievents"]
    ]
  },

  "government_Agreements_Treaties": {
    "parent_group": "government",
    "secondary_type": "Agreements/Treaties",
    "description": "A governmental event involving the acceptance, rejection, violation, or negotiation of formal agreements or treaties.",
    "original_event_types": [
      ["government.agreements.acceptagreementcontractceasefire","rams"],
      ["government.agreements.n/a","rams"],
      ["government.agreements.rejectnullifyagreementcontractceasefire","rams"],
      ["government.agreements.violateagreement","rams"]
    ]
  },
  "government_Formation": {
    "parent_group": "government",
    "secondary_type": "Formation of Government/Organization",
    "description": "An event concerning the creation, merging, or restructuring of a governmental body or organization.",
    "original_event_types": [
      ["government.formation.mergegpe","rams"],
      ["government.formation.n/a","rams"],
      ["government.formation.startgpe","rams"]
    ]
  },
  "government_Legislation": {
    "parent_group": "government",
    "secondary_type": "Legislation",
    "description": "An event where laws or formal regulations are proposed, enacted, or modified.",
    "original_event_types": [
      ["government.legislate.legislate","rams"]
    ]
  },
  "government_Spying_Intelligence": {
    "parent_group": "government",
    "secondary_type": "Spying/Intelligence",
    "description": "An event involving espionage or intelligence-gathering activities conducted by governmental actors.",
    "original_event_types": [
      ["government.spy.spy","rams"]
    ]
  },
  "government_Vote_Election": {
    "parent_group": "government",
    "secondary_type": "Vote/Election",
    "description": "An event related to voting processes, casting ballots, or interference in elections.",
    "original_event_types": [
      ["government.vote.castvote","rams"],
      ["government.vote.n/a","rams"],
      ["government.vote.violationspreventvote","rams"]
    ]
  },

  "inspection_Sensory_Observation_Inspection": {
    "parent_group": "inspection",
    "secondary_type": "Sensory Observation/Inspection",
    "description": "An event involving monitoring, observing, or physically inspecting people, organizations, or processes.",
    "original_event_types": [
      ["inspection.sensoryobserve.inspectpeopleorganization","rams"],
      ["inspection.sensoryobserve.monitorelection","rams"],
      ["inspection.sensoryobserve.n/a","rams"],
      ["inspection.sensoryobserve.physicalinvestigateinspect","rams"]
    ]
  },

  "manufacture_Artifact_Manufacturing_Assembly": {
    "parent_group": "manufacture",
    "secondary_type": "Artifact Manufacturing/Assembly",
    "description": "An event in which a tangible object or intellectual property is created, built, or manufactured.",
    "original_event_types": [
      ["manufacture.artifact.build","rams"],
      ["manufacture.artifact.createintellectualproperty","rams"],
      ["manufacture.artifact.createmanufacture","rams"],
      ["manufacture.artifact.n/a","rams"]
    ]
  },

  "personnel_Elect_Appointment": {
    "parent_group": "personnel",
    "secondary_type": "Elect/Appointment",
    "description": "An event where an individual is elected or formally appointed to a position.",
    "original_event_types": [
      ["personnel.elect.n/a","rams"],
      ["personnel.elect.winelection","rams"]
    ]
  },
  "personnel_Start_Position_Hiring": {
    "parent_group": "personnel",
    "secondary_type": "Start Position/Hiring",
    "description": "An event in which a person begins employment or assumes a new role.",
    "original_event_types": [
      ["personnel.startposition.hiring","rams"],
      ["personnel.startposition.n/a","rams"]
    ]
  },
  "personnel_End_Position_Termination": {
    "parent_group": "personnel",
    "secondary_type": "End Position/Termination",
    "description": "An event where a person leaves a position due to resignation, retirement, firing, or layoff.",
    "original_event_types": [
      ["personnel.endposition.firinglayoff","rams"],
      ["personnel.endposition.n/a","rams"],
      ["personnel.endposition.quitretire","rams"],
      ["Personnel.EndPosition.Unspecified","wikievents"]
    ]
  },
  "personnel_General": {
    "parent_group": "personnel",
    "secondary_type": "General Personnel Events",
    "description": "A general personnel-related event without a specifically defined employment transition.",
    "original_event_types": [
      ["Personnel.StartPosition.Unspecified","wikievents"]
    ]
  },

  "cognitive_Identify_Categorize": {
    "parent_group": "cognitive",
    "secondary_type": "Identify/Categorize",
    "description": "A cognitive event involving recognizing, labeling, or classifying an entity or concept.",
    "original_event_types": [
      ["Cognitive.IdentifyCategorize.Unspecified","wikievents"]
    ]
  },
  "cognitive_Inspection_Observation": {
    "parent_group": "cognitive",
    "secondary_type": "Inspection/Sensory Observation",
    "description": "A cognitive event involving perceptual observation or examination.",
    "original_event_types": [
      ["Cognitive.Inspection.SensoryObserve","wikievents"]
    ]
  },
  "cognitive_Research_Learning": {
    "parent_group": "cognitive",
    "secondary_type": "Research/Learning",
    "description": "A cognitive event involving investigation, study, or acquisition of knowledge.",
    "original_event_types": [
      ["Cognitive.Research.Unspecified","wikievents"]
    ]
  },
  "cognitive_Teaching_Training": {
    "parent_group": "cognitive",
    "secondary_type": "Teaching/Training",
    "description": "A cognitive event where knowledge or skills are intentionally transmitted through teaching or training.",
    "original_event_types": [
      ["Cognitive.TeachingTrainingLearning.Unspecified","wikievents"]
    ]
  },

  "control_Impede_Interfere_With": {
    "parent_group": "control",
    "secondary_type": "Impede/Interfere With",
    "description": "An event involving obstruction, restriction, or interference with an action or process.",
    "original_event_types": [
      ["Control.ImpedeInterfereWith.Unspecified","wikievents"]
    ]
  },

  "genericcrime_Generic_Crime": {
    "parent_group": "genericcrime",
    "secondary_type": "Generic Crime",
    "description": "A broadly defined criminal activity that does not fall into a more specific crime category.",
    "original_event_types": [
      ["GenericCrime.GenericCrime.GenericCrime","wikievents"]
    ]
  },

  "medical_Medical_Intervention": {
    "parent_group": "medical",
    "secondary_type": "Medical Intervention",
    "description": "An event involving medical treatment or intervention aimed at improving or stabilizing health.",
    "original_event_types": [
      ["Medical.Intervention.Unspecified","wikievents"]
    ]
  }
}

original_new_event_type_mappings = {
  'm2e2': [['Conflict:Attack', 'conflict_Attack'],
  ['Conflict:Demonstrate', 'conflict_Demonstrate'],
  ['Contact:Meet', 'contact_Meet_Correspond'],
  ['Contact:Phone-Write', 'contact_Meet_Correspond'],
  ['Justice:Arrest-Jail', 'justice_Arrest_Jail_Detain'],
  ['Life:Die', 'life_Die_Death'],
  ['Movement:Transport', 'movement_Transport_Artifact'],
  ['Transaction:Transfer-Money', 'transaction_Transfer_Money']],
 'rams': [['conflict.attack.airstrikemissilestrike', 'conflict_Attack'],
  ['conflict.attack.biologicalchemicalpoisonattack', 'conflict_Attack'],
  ['conflict.attack.bombing', 'conflict_Attack'],
  ['conflict.attack.firearmattack', 'conflict_Attack'],
  ['conflict.attack.hanging', 'conflict_Attack'],
  ['conflict.attack.invade', 'conflict_Attack'],
  ['conflict.attack.n/a', 'conflict_Attack'],
  ['conflict.attack.selfdirectedbattle', 'conflict_Attack'],
  ['conflict.attack.setfire', 'conflict_Attack'],
  ['conflict.attack.stabbing', 'conflict_Attack'],
  ['conflict.attack.stealrobhijack', 'conflict_Attack'],
  ['conflict.attack.strangling', 'conflict_Attack'],
  ['conflict.demonstrate.marchprotestpoliticalgathering',
   'conflict_Demonstrate'],
  ['conflict.demonstrate.n/a', 'conflict_Demonstrate'],
  ['conflict.yield.n/a', 'conflict_Yield'],
  ['conflict.yield.retreat', 'conflict_Yield'],
  ['conflict.yield.surrender', 'conflict_Yield'],
  ['contact.collaborate.correspondence', 'contact_Meet_Correspond'],
  ['contact.collaborate.meet', 'contact_Meet_Correspond'],
  ['contact.collaborate.n/a', 'contact_Meet_Correspond'],
  ['contact.negotiate.correspondence', 'contact_Meet_Correspond'],
  ['contact.negotiate.meet', 'contact_Meet_Correspond'],
  ['contact.negotiate.n/a', 'contact_Meet_Correspond'],
  ['contact.discussion.correspondence', 'contact_Meet_Correspond'],
  ['contact.discussion.meet', 'contact_Meet_Correspond'],
  ['contact.discussion.n/a', 'contact_Meet_Correspond'],
  ['contact.funeralvigil.meet', 'contact_Meet_Correspond'],
  ['contact.funeralvigil.n/a', 'contact_Meet_Correspond'],
  ['contact.mediastatement.broadcast', 'contact_Broadcast_Public_Statement'],
  ['contact.mediastatement.n/a', 'contact_Broadcast_Public_Statement'],
  ['contact.publicstatementinperson.broadcast',
   'contact_Broadcast_Public_Statement'],
  ['contact.publicstatementinperson.n/a', 'contact_Broadcast_Public_Statement'],
  ['contact.commandorder.broadcast', 'contact_Command_Order_Request'],
  ['contact.commandorder.correspondence', 'contact_Command_Order_Request'],
  ['contact.commandorder.meet', 'contact_Command_Order_Request'],
  ['contact.commandorder.n/a', 'contact_Command_Order_Request'],
  ['contact.commitmentpromiseexpressintent.broadcast',
   'contact_Command_Order_Request'],
  ['contact.commitmentpromiseexpressintent.correspondence',
   'contact_Command_Order_Request'],
  ['contact.commitmentpromiseexpressintent.meet',
   'contact_Command_Order_Request'],
  ['contact.commitmentpromiseexpressintent.n/a',
   'contact_Command_Order_Request'],
  ['contact.requestadvise.broadcast', 'contact_Command_Order_Request'],
  ['contact.requestadvise.correspondence', 'contact_Command_Order_Request'],
  ['contact.requestadvise.meet', 'contact_Command_Order_Request'],
  ['contact.requestadvise.n/a', 'contact_Command_Order_Request'],
  ['contact.threatencoerce.broadcast',
   'contact_Threaten_Coerce_Prevarication'],
  ['contact.threatencoerce.correspondence',
   'contact_Threaten_Coerce_Prevarication'],
  ['contact.threatencoerce.meet', 'contact_Threaten_Coerce_Prevarication'],
  ['contact.threatencoerce.n/a', 'contact_Threaten_Coerce_Prevarication'],
  ['contact.prevarication.broadcast', 'contact_Threaten_Coerce_Prevarication'],
  ['contact.prevarication.correspondence',
   'contact_Threaten_Coerce_Prevarication'],
  ['contact.prevarication.meet', 'contact_Threaten_Coerce_Prevarication'],
  ['contact.prevarication.n/a', 'contact_Threaten_Coerce_Prevarication'],
  ['justice.arrestjaildetain.arrestjaildetain', 'justice_Arrest_Jail_Detain'],
  ['justice.initiatejudicialprocess.chargeindict',
   'justice_Initiate_Judicial_Process'],
  ['justice.initiatejudicialprocess.n/a', 'justice_Initiate_Judicial_Process'],
  ['justice.initiatejudicialprocess.trialhearing',
   'justice_Initiate_Judicial_Process'],
  ['justice.investigate.investigatecrime', 'justice_Investigate'],
  ['justice.investigate.n/a', 'justice_Investigate'],
  ['justice.judicialconsequences.convict', 'justice_Judicial_Consequences'],
  ['justice.judicialconsequences.execute', 'justice_Judicial_Consequences'],
  ['justice.judicialconsequences.extradite', 'justice_Judicial_Consequences'],
  ['justice.judicialconsequences.n/a', 'justice_Judicial_Consequences'],
  ['life.die.deathcausedbyviolentevents', 'life_Die_Death'],
  ['life.die.n/a', 'life_Die_Death'],
  ['life.die.nonviolentdeath', 'life_Die_Death'],
  ['life.injure.illnessdegradationhungerthirst', 'life_Injure_Harm'],
  ['life.injure.illnessdegradationphysical', 'life_Injure_Harm'],
  ['life.injure.injurycausedbyviolentevents', 'life_Injure_Harm'],
  ['life.injure.n/a', 'life_Injure_Harm'],
  ['movement.transportartifact.bringcarryunload',
   'movement_Transport_Artifact'],
  ['movement.transportartifact.disperseseparate',
   'movement_Transport_Artifact'],
  ['movement.transportartifact.fall', 'movement_Transport_Artifact'],
  ['movement.transportartifact.grantentry', 'movement_Transport_Artifact'],
  ['movement.transportartifact.hide', 'movement_Transport_Artifact'],
  ['movement.transportartifact.n/a', 'movement_Transport_Artifact'],
  ['movement.transportartifact.nonviolentthrowlaunch',
   'movement_Transport_Artifact'],
  ['movement.transportartifact.prevententry', 'movement_Transport_Artifact'],
  ['movement.transportartifact.preventexit', 'movement_Transport_Artifact'],
  ['movement.transportartifact.receiveimport', 'movement_Transport_Artifact'],
  ['movement.transportartifact.sendsupplyexport',
   'movement_Transport_Artifact'],
  ['movement.transportartifact.smuggleextract', 'movement_Transport_Artifact'],
  ['movement.transportperson.bringcarryunload', 'movement_Transport_Person'],
  ['movement.transportperson.disperseseparate', 'movement_Transport_Person'],
  ['movement.transportperson.evacuationrescue', 'movement_Transport_Person'],
  ['movement.transportperson.fall', 'movement_Transport_Person'],
  ['movement.transportperson.grantentryasylum', 'movement_Transport_Person'],
  ['movement.transportperson.hide', 'movement_Transport_Person'],
  ['movement.transportperson.n/a', 'movement_Transport_Person'],
  ['movement.transportperson.prevententry', 'movement_Transport_Person'],
  ['movement.transportperson.preventexit', 'movement_Transport_Person'],
  ['movement.transportperson.selfmotion', 'movement_Transport_Person'],
  ['movement.transportperson.smuggleextract', 'movement_Transport_Person'],
  ['transaction.transfermoney.borrowlend', 'transaction_Transfer_Money'],
  ['transaction.transfermoney.embargosanction', 'transaction_Transfer_Money'],
  ['transaction.transfermoney.giftgrantprovideaid',
   'transaction_Transfer_Money'],
  ['transaction.transfermoney.n/a', 'transaction_Transfer_Money'],
  ['transaction.transfermoney.payforservice', 'transaction_Transfer_Money'],
  ['transaction.transfermoney.purchase', 'transaction_Transfer_Money'],
  ['transaction.transaction.embargosanction',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transaction.giftgrantprovideaid',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transaction.n/a', 'transaction_Transfer_Ownership_Control'],
  ['transaction.transaction.transfercontrol',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transferownership.borrowlend',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transferownership.embargosanction',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transferownership.giftgrantprovideaid',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transferownership.n/a',
   'transaction_Transfer_Ownership_Control'],
  ['transaction.transferownership.purchase',
   'transaction_Transfer_Ownership_Control'],
  ['artifactexistence.damagedestroy.damage',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['artifactexistence.damagedestroy.destroy',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['artifactexistence.damagedestroy.n/a',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['disaster.accidentcrash.accidentcrash', 'disaster_Accident_Crash'],
  ['disaster.fireexplosion.fireexplosion', 'disaster_Fire_Explosion'],
  ['government.agreements.acceptagreementcontractceasefire',
   'government_Agreements_Treaties'],
  ['government.agreements.n/a', 'government_Agreements_Treaties'],
  ['government.agreements.rejectnullifyagreementcontractceasefire',
   'government_Agreements_Treaties'],
  ['government.agreements.violateagreement', 'government_Agreements_Treaties'],
  ['government.formation.mergegpe', 'government_Formation'],
  ['government.formation.n/a', 'government_Formation'],
  ['government.formation.startgpe', 'government_Formation'],
  ['government.legislate.legislate', 'government_Legislation'],
  ['government.spy.spy', 'government_Spying_Intelligence'],
  ['government.vote.castvote', 'government_Vote_Election'],
  ['government.vote.n/a', 'government_Vote_Election'],
  ['government.vote.violationspreventvote', 'government_Vote_Election'],
  ['inspection.sensoryobserve.inspectpeopleorganization',
   'inspection_Sensory_Observation_Inspection'],
  ['inspection.sensoryobserve.monitorelection',
   'inspection_Sensory_Observation_Inspection'],
  ['inspection.sensoryobserve.n/a',
   'inspection_Sensory_Observation_Inspection'],
  ['inspection.sensoryobserve.physicalinvestigateinspect',
   'inspection_Sensory_Observation_Inspection'],
  ['manufacture.artifact.build',
   'manufacture_Artifact_Manufacturing_Assembly'],
  ['manufacture.artifact.createintellectualproperty',
   'manufacture_Artifact_Manufacturing_Assembly'],
  ['manufacture.artifact.createmanufacture',
   'manufacture_Artifact_Manufacturing_Assembly'],
  ['manufacture.artifact.n/a', 'manufacture_Artifact_Manufacturing_Assembly'],
  ['personnel.elect.n/a', 'personnel_Elect_Appointment'],
  ['personnel.elect.winelection', 'personnel_Elect_Appointment'],
  ['personnel.startposition.hiring', 'personnel_Start_Position_Hiring'],
  ['personnel.startposition.n/a', 'personnel_Start_Position_Hiring'],
  ['personnel.endposition.firinglayoff', 'personnel_End_Position_Termination'],
  ['personnel.endposition.n/a', 'personnel_End_Position_Termination'],
  ['personnel.endposition.quitretire', 'personnel_End_Position_Termination']],
 'wikievents': [['Conflict.Attack.DetonateExplode', 'conflict_Attack'],
  ['Conflict.Attack.Unspecified', 'conflict_Attack'],
  ['Conflict.Demonstrate.DemonstrateWithViolence', 'conflict_Demonstrate'],
  ['Conflict.Demonstrate.Unspecified', 'conflict_Demonstrate'],
  ['Conflict.Defeat.Unspecified', 'conflict_Yield'],
  ['Contact.RequestCommand.Broadcast', 'contact_Command_Order_Request'],
  ['Contact.RequestCommand.Correspondence', 'contact_Command_Order_Request'],
  ['Contact.RequestCommand.Meet', 'contact_Command_Order_Request'],
  ['Contact.RequestCommand.Unspecified', 'contact_Command_Order_Request'],
  ['Contact.ThreatenCoerce.Broadcast',
   'contact_Threaten_Coerce_Prevarication'],
  ['Contact.ThreatenCoerce.Correspondence',
   'contact_Threaten_Coerce_Prevarication'],
  ['Contact.ThreatenCoerce.Unspecified',
   'contact_Threaten_Coerce_Prevarication'],
  ['Contact.Contact.Broadcast', 'contact_General_Contact'],
  ['Contact.Contact.Correspondence', 'contact_General_Contact'],
  ['Contact.Contact.Meet', 'contact_General_Contact'],
  ['Contact.Contact.Unspecified', 'contact_General_Contact'],
  ['Justice.ArrestJailDetain.Unspecified', 'justice_Arrest_Jail_Detain'],
  ['Justice.ChargeIndict.Unspecified', 'justice_Initiate_Judicial_Process'],
  ['Justice.TrialHearing.Unspecified', 'justice_Initiate_Judicial_Process'],
  ['Justice.InvestigateCrime.Unspecified', 'justice_Investigate'],
  ['Justice.Acquit.Unspecified', 'justice_Judicial_Consequences'],
  ['Justice.Convict.Unspecified', 'justice_Judicial_Consequences'],
  ['Justice.ReleaseParole.Unspecified', 'justice_Judicial_Consequences'],
  ['Justice.Sentence.Unspecified', 'justice_Judicial_Consequences'],
  ['Life.Die.Unspecified', 'life_Die_Death'],
  ['Life.Injure.Unspecified', 'life_Injure_Harm'],
  ['Life.Infect.Unspecified', 'life_Infect_Disease'],
  ['Movement.Transportation.Evacuation', 'movement_General_Transportation'],
  ['Movement.Transportation.IllegalTransportation',
   'movement_General_Transportation'],
  ['Movement.Transportation.PreventPassage',
   'movement_General_Transportation'],
  ['Movement.Transportation.Unspecified', 'movement_General_Transportation'],
  ['Transaction.Donation.Unspecified',
   'transaction_Transfer_Ownership_Control'],
  ['Transaction.ExchangeBuySell.Unspecified',
   'transaction_Transfer_Ownership_Control'],
  ['ArtifactExistence.DamageDestroyDisableDismantle.Damage',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['ArtifactExistence.DamageDestroyDisableDismantle.Destroy',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['ArtifactExistence.DamageDestroyDisableDismantle.DisableDefuse',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['ArtifactExistence.DamageDestroyDisableDismantle.Dismantle',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['ArtifactExistence.DamageDestroyDisableDismantle.Unspecified',
   'artifact_existence_Damage_Destroy_Disable_Dismantle'],
  ['ArtifactExistence.ManufactureAssemble.Unspecified',
   'artifact_existence_Manufacture_Assemble'],
  ['Disaster.Crash.Unspecified', 'disaster_Accident_Crash'],
  ['Disaster.DiseaseOutbreak.Unspecified', 'disaster_Disease_Outbreak'],
  ['Personnel.EndPosition.Unspecified', 'personnel_End_Position_Termination'],
  ['Personnel.StartPosition.Unspecified', 'personnel_General'],
  ['Cognitive.IdentifyCategorize.Unspecified',
   'cognitive_Identify_Categorize'],
  ['Cognitive.Inspection.SensoryObserve', 'cognitive_Inspection_Observation'],
  ['Cognitive.Research.Unspecified', 'cognitive_Research_Learning'],
  ['Cognitive.TeachingTrainingLearning.Unspecified',
   'cognitive_Teaching_Training'],
  ['Control.ImpedeInterfereWith.Unspecified', 'control_Impede_Interfere_With'],
  ['GenericCrime.GenericCrime.GenericCrime', 'genericcrime_Generic_Crime'],
  ['Medical.Intervention.Unspecified', 'medical_Medical_Intervention']]}

original_new_event_type_mappings_dict = {'m2e2': {'Conflict:Attack': 'conflict_Attack',
  'Conflict:Demonstrate': 'conflict_Demonstrate',
  'Contact:Meet': 'contact_Meet_Correspond',
  'Contact:Phone-Write': 'contact_Meet_Correspond',
  'Justice:Arrest-Jail': 'justice_Arrest_Jail_Detain',
  'Life:Die': 'life_Die_Death',
  'Movement:Transport': 'movement_Transport_Artifact',
  'Transaction:Transfer-Money': 'transaction_Transfer_Money'},
 'rams': {'conflict.attack.airstrikemissilestrike': 'conflict_Attack',
  'conflict.attack.biologicalchemicalpoisonattack': 'conflict_Attack',
  'conflict.attack.bombing': 'conflict_Attack',
  'conflict.attack.firearmattack': 'conflict_Attack',
  'conflict.attack.hanging': 'conflict_Attack',
  'conflict.attack.invade': 'conflict_Attack',
  'conflict.attack.n/a': 'conflict_Attack',
  'conflict.attack.selfdirectedbattle': 'conflict_Attack',
  'conflict.attack.setfire': 'conflict_Attack',
  'conflict.attack.stabbing': 'conflict_Attack',
  'conflict.attack.stealrobhijack': 'conflict_Attack',
  'conflict.attack.strangling': 'conflict_Attack',
  'conflict.demonstrate.marchprotestpoliticalgathering': 'conflict_Demonstrate',
  'conflict.demonstrate.n/a': 'conflict_Demonstrate',
  'conflict.yield.n/a': 'conflict_Yield',
  'conflict.yield.retreat': 'conflict_Yield',
  'conflict.yield.surrender': 'conflict_Yield',
  'contact.collaborate.correspondence': 'contact_Meet_Correspond',
  'contact.collaborate.meet': 'contact_Meet_Correspond',
  'contact.collaborate.n/a': 'contact_Meet_Correspond',
  'contact.negotiate.correspondence': 'contact_Meet_Correspond',
  'contact.negotiate.meet': 'contact_Meet_Correspond',
  'contact.negotiate.n/a': 'contact_Meet_Correspond',
  'contact.discussion.correspondence': 'contact_Meet_Correspond',
  'contact.discussion.meet': 'contact_Meet_Correspond',
  'contact.discussion.n/a': 'contact_Meet_Correspond',
  'contact.funeralvigil.meet': 'contact_Meet_Correspond',
  'contact.funeralvigil.n/a': 'contact_Meet_Correspond',
  'contact.mediastatement.broadcast': 'contact_Broadcast_Public_Statement',
  'contact.mediastatement.n/a': 'contact_Broadcast_Public_Statement',
  'contact.publicstatementinperson.broadcast': 'contact_Broadcast_Public_Statement',
  'contact.publicstatementinperson.n/a': 'contact_Broadcast_Public_Statement',
  'contact.commandorder.broadcast': 'contact_Command_Order_Request',
  'contact.commandorder.correspondence': 'contact_Command_Order_Request',
  'contact.commandorder.meet': 'contact_Command_Order_Request',
  'contact.commandorder.n/a': 'contact_Command_Order_Request',
  'contact.commitmentpromiseexpressintent.broadcast': 'contact_Command_Order_Request',
  'contact.commitmentpromiseexpressintent.correspondence': 'contact_Command_Order_Request',
  'contact.commitmentpromiseexpressintent.meet': 'contact_Command_Order_Request',
  'contact.commitmentpromiseexpressintent.n/a': 'contact_Command_Order_Request',
  'contact.requestadvise.broadcast': 'contact_Command_Order_Request',
  'contact.requestadvise.correspondence': 'contact_Command_Order_Request',
  'contact.requestadvise.meet': 'contact_Command_Order_Request',
  'contact.requestadvise.n/a': 'contact_Command_Order_Request',
  'contact.threatencoerce.broadcast': 'contact_Threaten_Coerce_Prevarication',
  'contact.threatencoerce.correspondence': 'contact_Threaten_Coerce_Prevarication',
  'contact.threatencoerce.meet': 'contact_Threaten_Coerce_Prevarication',
  'contact.threatencoerce.n/a': 'contact_Threaten_Coerce_Prevarication',
  'contact.prevarication.broadcast': 'contact_Threaten_Coerce_Prevarication',
  'contact.prevarication.correspondence': 'contact_Threaten_Coerce_Prevarication',
  'contact.prevarication.meet': 'contact_Threaten_Coerce_Prevarication',
  'contact.prevarication.n/a': 'contact_Threaten_Coerce_Prevarication',
  'justice.arrestjaildetain.arrestjaildetain': 'justice_Arrest_Jail_Detain',
  'justice.initiatejudicialprocess.chargeindict': 'justice_Initiate_Judicial_Process',
  'justice.initiatejudicialprocess.n/a': 'justice_Initiate_Judicial_Process',
  'justice.initiatejudicialprocess.trialhearing': 'justice_Initiate_Judicial_Process',
  'justice.investigate.investigatecrime': 'justice_Investigate',
  'justice.investigate.n/a': 'justice_Investigate',
  'justice.judicialconsequences.convict': 'justice_Judicial_Consequences',
  'justice.judicialconsequences.execute': 'justice_Judicial_Consequences',
  'justice.judicialconsequences.extradite': 'justice_Judicial_Consequences',
  'justice.judicialconsequences.n/a': 'justice_Judicial_Consequences',
  'life.die.deathcausedbyviolentevents': 'life_Die_Death',
  'life.die.n/a': 'life_Die_Death',
  'life.die.nonviolentdeath': 'life_Die_Death',
  'life.injure.illnessdegradationhungerthirst': 'life_Injure_Harm',
  'life.injure.illnessdegradationphysical': 'life_Injure_Harm',
  'life.injure.injurycausedbyviolentevents': 'life_Injure_Harm',
  'life.injure.n/a': 'life_Injure_Harm',
  'movement.transportartifact.bringcarryunload': 'movement_Transport_Artifact',
  'movement.transportartifact.disperseseparate': 'movement_Transport_Artifact',
  'movement.transportartifact.fall': 'movement_Transport_Artifact',
  'movement.transportartifact.grantentry': 'movement_Transport_Artifact',
  'movement.transportartifact.hide': 'movement_Transport_Artifact',
  'movement.transportartifact.n/a': 'movement_Transport_Artifact',
  'movement.transportartifact.nonviolentthrowlaunch': 'movement_Transport_Artifact',
  'movement.transportartifact.prevententry': 'movement_Transport_Artifact',
  'movement.transportartifact.preventexit': 'movement_Transport_Artifact',
  'movement.transportartifact.receiveimport': 'movement_Transport_Artifact',
  'movement.transportartifact.sendsupplyexport': 'movement_Transport_Artifact',
  'movement.transportartifact.smuggleextract': 'movement_Transport_Artifact',
  'movement.transportperson.bringcarryunload': 'movement_Transport_Person',
  'movement.transportperson.disperseseparate': 'movement_Transport_Person',
  'movement.transportperson.evacuationrescue': 'movement_Transport_Person',
  'movement.transportperson.fall': 'movement_Transport_Person',
  'movement.transportperson.grantentryasylum': 'movement_Transport_Person',
  'movement.transportperson.hide': 'movement_Transport_Person',
  'movement.transportperson.n/a': 'movement_Transport_Person',
  'movement.transportperson.prevententry': 'movement_Transport_Person',
  'movement.transportperson.preventexit': 'movement_Transport_Person',
  'movement.transportperson.selfmotion': 'movement_Transport_Person',
  'movement.transportperson.smuggleextract': 'movement_Transport_Person',
  'transaction.transfermoney.borrowlend': 'transaction_Transfer_Money',
  'transaction.transfermoney.embargosanction': 'transaction_Transfer_Money',
  'transaction.transfermoney.giftgrantprovideaid': 'transaction_Transfer_Money',
  'transaction.transfermoney.n/a': 'transaction_Transfer_Money',
  'transaction.transfermoney.payforservice': 'transaction_Transfer_Money',
  'transaction.transfermoney.purchase': 'transaction_Transfer_Money',
  'transaction.transaction.embargosanction': 'transaction_Transfer_Ownership_Control',
  'transaction.transaction.giftgrantprovideaid': 'transaction_Transfer_Ownership_Control',
  'transaction.transaction.n/a': 'transaction_Transfer_Ownership_Control',
  'transaction.transaction.transfercontrol': 'transaction_Transfer_Ownership_Control',
  'transaction.transferownership.borrowlend': 'transaction_Transfer_Ownership_Control',
  'transaction.transferownership.embargosanction': 'transaction_Transfer_Ownership_Control',
  'transaction.transferownership.giftgrantprovideaid': 'transaction_Transfer_Ownership_Control',
  'transaction.transferownership.n/a': 'transaction_Transfer_Ownership_Control',
  'transaction.transferownership.purchase': 'transaction_Transfer_Ownership_Control',
  'artifactexistence.damagedestroy.damage': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'artifactexistence.damagedestroy.destroy': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'artifactexistence.damagedestroy.n/a': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'disaster.accidentcrash.accidentcrash': 'disaster_Accident_Crash',
  'disaster.fireexplosion.fireexplosion': 'disaster_Fire_Explosion',
  'government.agreements.acceptagreementcontractceasefire': 'government_Agreements_Treaties',
  'government.agreements.n/a': 'government_Agreements_Treaties',
  'government.agreements.rejectnullifyagreementcontractceasefire': 'government_Agreements_Treaties',
  'government.agreements.violateagreement': 'government_Agreements_Treaties',
  'government.formation.mergegpe': 'government_Formation',
  'government.formation.n/a': 'government_Formation',
  'government.formation.startgpe': 'government_Formation',
  'government.legislate.legislate': 'government_Legislation',
  'government.spy.spy': 'government_Spying_Intelligence',
  'government.vote.castvote': 'government_Vote_Election',
  'government.vote.n/a': 'government_Vote_Election',
  'government.vote.violationspreventvote': 'government_Vote_Election',
  'inspection.sensoryobserve.inspectpeopleorganization': 'inspection_Sensory_Observation_Inspection',
  'inspection.sensoryobserve.monitorelection': 'inspection_Sensory_Observation_Inspection',
  'inspection.sensoryobserve.n/a': 'inspection_Sensory_Observation_Inspection',
  'inspection.sensoryobserve.physicalinvestigateinspect': 'inspection_Sensory_Observation_Inspection',
  'manufacture.artifact.build': 'manufacture_Artifact_Manufacturing_Assembly',
  'manufacture.artifact.createintellectualproperty': 'manufacture_Artifact_Manufacturing_Assembly',
  'manufacture.artifact.createmanufacture': 'manufacture_Artifact_Manufacturing_Assembly',
  'manufacture.artifact.n/a': 'manufacture_Artifact_Manufacturing_Assembly',
  'personnel.elect.n/a': 'personnel_Elect_Appointment',
  'personnel.elect.winelection': 'personnel_Elect_Appointment',
  'personnel.startposition.hiring': 'personnel_Start_Position_Hiring',
  'personnel.startposition.n/a': 'personnel_Start_Position_Hiring',
  'personnel.endposition.firinglayoff': 'personnel_End_Position_Termination',
  'personnel.endposition.n/a': 'personnel_End_Position_Termination',
  'personnel.endposition.quitretire': 'personnel_End_Position_Termination'},
 'wikievents': {'Conflict.Attack.DetonateExplode': 'conflict_Attack',
  'Conflict.Attack.Unspecified': 'conflict_Attack',
  'Conflict.Demonstrate.DemonstrateWithViolence': 'conflict_Demonstrate',
  'Conflict.Demonstrate.Unspecified': 'conflict_Demonstrate',
  'Conflict.Defeat.Unspecified': 'conflict_Yield',
  'Contact.RequestCommand.Broadcast': 'contact_Command_Order_Request',
  'Contact.RequestCommand.Correspondence': 'contact_Command_Order_Request',
  'Contact.RequestCommand.Meet': 'contact_Command_Order_Request',
  'Contact.RequestCommand.Unspecified': 'contact_Command_Order_Request',
  'Contact.ThreatenCoerce.Broadcast': 'contact_Threaten_Coerce_Prevarication',
  'Contact.ThreatenCoerce.Correspondence': 'contact_Threaten_Coerce_Prevarication',
  'Contact.ThreatenCoerce.Unspecified': 'contact_Threaten_Coerce_Prevarication',
  'Contact.Contact.Broadcast': 'contact_General_Contact',
  'Contact.Contact.Correspondence': 'contact_General_Contact',
  'Contact.Contact.Meet': 'contact_General_Contact',
  'Contact.Contact.Unspecified': 'contact_General_Contact',
  'Justice.ArrestJailDetain.Unspecified': 'justice_Arrest_Jail_Detain',
  'Justice.ChargeIndict.Unspecified': 'justice_Initiate_Judicial_Process',
  'Justice.TrialHearing.Unspecified': 'justice_Initiate_Judicial_Process',
  'Justice.InvestigateCrime.Unspecified': 'justice_Investigate',
  'Justice.Acquit.Unspecified': 'justice_Judicial_Consequences',
  'Justice.Convict.Unspecified': 'justice_Judicial_Consequences',
  'Justice.ReleaseParole.Unspecified': 'justice_Judicial_Consequences',
  'Justice.Sentence.Unspecified': 'justice_Judicial_Consequences',
  'Life.Die.Unspecified': 'life_Die_Death',
  'Life.Injure.Unspecified': 'life_Injure_Harm',
  'Life.Infect.Unspecified': 'life_Infect_Disease',
  'Movement.Transportation.Evacuation': 'movement_General_Transportation',
  'Movement.Transportation.IllegalTransportation': 'movement_General_Transportation',
  'Movement.Transportation.PreventPassage': 'movement_General_Transportation',
  'Movement.Transportation.Unspecified': 'movement_General_Transportation',
  'Transaction.Donation.Unspecified': 'transaction_Transfer_Ownership_Control',
  'Transaction.ExchangeBuySell.Unspecified': 'transaction_Transfer_Ownership_Control',
  'ArtifactExistence.DamageDestroyDisableDismantle.Damage': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'ArtifactExistence.DamageDestroyDisableDismantle.Destroy': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'ArtifactExistence.DamageDestroyDisableDismantle.DisableDefuse': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'ArtifactExistence.DamageDestroyDisableDismantle.Dismantle': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'ArtifactExistence.DamageDestroyDisableDismantle.Unspecified': 'artifact_existence_Damage_Destroy_Disable_Dismantle',
  'ArtifactExistence.ManufactureAssemble.Unspecified': 'artifact_existence_Manufacture_Assemble',
  'Disaster.Crash.Unspecified': 'disaster_Accident_Crash',
  'Disaster.DiseaseOutbreak.Unspecified': 'disaster_Disease_Outbreak',
  'Personnel.EndPosition.Unspecified': 'personnel_End_Position_Termination',
  'Personnel.StartPosition.Unspecified': 'personnel_General',
  'Cognitive.IdentifyCategorize.Unspecified': 'cognitive_Identify_Categorize',
  'Cognitive.Inspection.SensoryObserve': 'cognitive_Inspection_Observation',
  'Cognitive.Research.Unspecified': 'cognitive_Research_Learning',
  'Cognitive.TeachingTrainingLearning.Unspecified': 'cognitive_Teaching_Training',
  'Control.ImpedeInterfereWith.Unspecified': 'control_Impede_Interfere_With',
  'GenericCrime.GenericCrime.GenericCrime': 'genericcrime_Generic_Crime',
  'Medical.Intervention.Unspecified': 'medical_Medical_Intervention'}}

new_event_argument_roles_patterns = {'conflict_Attack': ['Attacker',
  'Target',
  'Artifact',
  'Place',
  'Instrument'],
 'conflict_Demonstrate': ['Entity',
  'Target',
  'Place',
  'Police',
  'Topic',
  'Regulator',
  'Demonstrator'],
 'contact_Meet_Correspond': ['Participant', 'Deceased', 'Place'],
 'justice_Arrest_Jail_Detain': ['Crime',
  'Detainee',
  'Place',
  'Jailer'],
 'life_Die_Death': ['Killer', 'Victim', 'Place', 'Instrument'],
 'movement_Transport_Artifact': ['Hiding_Place',
  'Vehicle',
  'Preventer',
  'Origin',
  'Artifact',
  'Destination',
  'Transporter'],
 'transaction_Transfer_Money': ['Giver',
  'Recipient',
  'Money',
  'Place',
  'Beneficiary',
  'Preventer'],
 'conflict_Yield': ['Recipient',
  'Victor',
  'Surrenderer',
  'Defeated',
  'Origin',
  'Place',
  'Retreater',
  'Destination'],
 'contact_Broadcast_Public_Statement': ['Place', 'Recipient', 'Communicator'],
 'contact_Command_Order_Request': ['Place',
  'Topic',
  'Recipient',
  'Communicator'],
 'contact_Threaten_Coerce_Prevarication': ['Place',
  'Recipient',
  'Communicator'],
 'justice_Initiate_Judicial_Process': ['Prosecutor',
  'Crime',
  'Defendant',
  'Place',
  'Judge_Court'],
 'justice_Investigate': ['Crime',
  'Observed_Entity',
  'Defendant',
  'Place',
  'Investigator'],
 'justice_Judicial_Consequences': ['Executioner',
  'Crime',
  'Defendant',
  'Origin',
  'Place',
  'Destination',
  'Judge_Court',
  'Extraditer'],
 'life_Injure_Harm': ['Victim', 'Body_Part', 'Place', 'Injurer', 'Instrument'],
 'movement_Transport_Person': ['Hiding_Place',
  'Preventer',
  'Granter',
  'Passenger',
  'Origin',
  'Vehicle',
  'Destination',
  'Transporter'],
 'transaction_Transfer_Ownership_Control': ['Giver',
  'Recipient',
  'Acquired_Entity',
  'Payment_Barter',
  'Territoryor_Facility',
  'Place',
  'Beneficiary',
  'Preventer'],
 'artifact_existence_Damage_Destroy_Disable_Dismantle': ['Damager',
  'Destroyer',
  'Disabler',
  'Dismantler',
  'Components',
  'Place',
  'Artifact',
  'Instrument'],
 'disaster_Accident_Crash': ['Vehicle',
  'Crash_Object',
  'Place',
  'Driver_Passenger'],
 'disaster_Fire_Explosion': ['Place', 'Fire_Explosion_Object', 'Instrument'],
 'government_Agreements_Treaties': ['Violator',
  'Participant',
  'Place',
  'Other_Participant',
  'Rejecter_Nullifier'],
 'government_Formation': ['Founder', 'Gpe', 'Participant', 'Place'],
 'government_Legislation': ['Government_Body', 'Law', 'Place'],
 'government_Spying_Intelligence': ['Beneficiary',
  'Place',
  'Spy',
  'Observed_Entity'],
 'government_Vote_Election': ['Ballot',
  'Candidate',
  'Result',
  'Voter',
  'Place',
  'Preventer'],
 'inspection_Sensory_Observation_Inspection': ['Monitored_Entity',
  'Observed_Entity',
  'Inspector',
  'Inspected_Entity',
  'Place',
  'Observer'],
 'manufacture_Artifact_Manufacturing_Assembly': ['Artifact',
  'Place',
  'Manufacturer',
  'Instrument'],
 'personnel_Elect_Appointment': ['Candidate', 'Voter', 'Place'],
 'personnel_Start_Position_Hiring': ['Employee',
  'Place_Of_Employment'],
 'personnel_End_Position_Termination': ['Employee',
  'Place_Of_Employment'],
 'contact_General_Contact': ['Recipient',
  'Communicator',
  'Participant',
  'Place',
  'Topic',
  'Instrument'],
 'life_Infect_Disease': ['Victim'],
 'movement_General_Transportation': ['Preventer',
  'Passenger_Artifact',
  'Origin',
  'Vehicle',
  'Destination',
  'Transporter'],
 'artifact_existence_Manufacture_Assemble': ['Manufacturer_Assembler',
  'Artifact',
  'Components',
  'Place'],
 'disaster_Disease_Outbreak': ['Victim', 'Place'],
 'personnel_General': ['Employee', 'Position', 'Place_Of_Employment'],
 'cognitive_Identify_Categorize': ['Identified_Role',
  'Place',
  'Identified_Object',
  'Identifier'],
 'cognitive_Inspection_Observation': ['Observed_Entity',
  'Observer',
  'Place',
  'Instrument'],
 'cognitive_Research_Learning': ['Researcher', 'Place', 'Subject'],
 'cognitive_Teaching_Training': ['Learner', 'Teacher_Trainer'],
 'control_Impede_Interfere_With': ['Impeder', 'Place'],
 'genericcrime_Generic_Crime': ['Victim', 'Perpetrator', 'Place'],
 'medical_Medical_Intervention': ['Treater', 'Patient', 'Place']}


# Keys are original dataset event types.
original_to_new_argument_role_lookup_m2e2 = {
 'm2e2': {
  'Conflict:Attack': {
   'Attacker': 'Attacker',
   'Target': 'Target',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'Conflict:Demonstrate': {
   'Entity': 'Entity',
   'Place': 'Place',
   'Police': 'Police'
  },
  'Contact:Meet': {
   'Entity': 'Participant',
   'Place': 'Place'
  },
  'Contact:Phone-Write': {
   'Entity': 'Participant',
   'Place': 'Place'
  },
  'Justice:Arrest-Jail': {
   'Person': 'Detainee',
   'Agent': 'Jailer',
   'Place': 'Place'
  },
  'Life:Die': {
   'Agent': 'Killer',
   'Victim': 'Victim',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'Movement:Transport': {
   'Artifact': 'Artifact',
   'Destination': 'Destination',
   'Origin': 'Origin',
   'Vehicle': 'Vehicle',
   'Agent': 'Transporter'
  },
  'Transaction:Transfer-Money': {
   'Giver': 'Giver',
   'Recipient': 'Recipient'
  }
 }
}


original_to_new_argument_role_lookup_wikievents = {
 'wikievents': {
  'ArtifactExistence.DamageDestroyDisableDismantle.Damage': {
   'Artifact': 'Artifact',
   'Damager': 'Damager',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'ArtifactExistence.DamageDestroyDisableDismantle.Destroy': {
   'Artifact': 'Artifact',
   'Destroyer': 'Destroyer',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'ArtifactExistence.DamageDestroyDisableDismantle.DisableDefuse': {
   'Artifact': 'Artifact',
   'Disabler': 'Disabler',
   'Instrument': 'Instrument'
  },
  'ArtifactExistence.DamageDestroyDisableDismantle.Dismantle': {
   'Artifact': 'Artifact',
   'Components': 'Components',
   'Dismantler': 'Dismantler',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'ArtifactExistence.DamageDestroyDisableDismantle.Unspecified': {
   'Artifact': 'Artifact',
   'DamagerDestroyer': 'Damager',
   'Instrument': 'Instrument',
   'Place': 'Place'
  },
  'ArtifactExistence.ManufactureAssemble.Unspecified': {
   'Artifact': 'Artifact',
   'Components': 'Components',
   'ManufacturerAssembler': 'Manufacturer_Assembler',
   'Place': 'Place'
  },
  'Cognitive.IdentifyCategorize.Unspecified': {
   'IdentifiedObject': 'Identified_Object',
   'IdentifiedRole': 'Identified_Role',
   'Identifier': 'Identifier',
   'Place': 'Place'
  },
  'Cognitive.Inspection.SensoryObserve': {
   'Instrument': 'Instrument',
   'ObservedEntity': 'Observed_Entity',
   'Observer': 'Observer',
   'Place': 'Place'
  },
  'Cognitive.Research.Unspecified': {
   'Place': 'Place',
   'Researcher': 'Researcher',
   'Subject': 'Subject'
  },
  'Cognitive.TeachingTrainingLearning.Unspecified': {
   'Learner': 'Learner',
   'TeacherTrainer': 'Teacher_Trainer'
  },
  'Conflict.Attack.DetonateExplode': {
   'Attacker': 'Attacker',
   'ExplosiveDevice': 'Instrument',
   'Instrument': 'Instrument',
   'Place': 'Place',
   'Target': 'Target'
  },
  'Conflict.Attack.Unspecified': {
   'Attacker': 'Attacker',
   'Instrument': 'Instrument',
   'Place': 'Place',
   'Target': 'Target'
  },
  'Conflict.Defeat.Unspecified': {
   'Defeated': 'Defeated',
   'Place': 'Place',
   'Victor': 'Victor'
  },
  'Conflict.Demonstrate.DemonstrateWithViolence': {
   'Demonstrator': 'Demonstrator',
   'Regulator': 'Regulator'
  },
  'Conflict.Demonstrate.Unspecified': {
   'Demonstrator': 'Demonstrator',
   'Target': 'Target',
   'Topic': 'Topic'
  },
  'Contact.Contact.Broadcast': {
   'Communicator': 'Communicator',
   'Instrument': 'Instrument',
   'Place': 'Place',
   'Recipient': 'Recipient',
   'Topic': 'Topic'
  },
  'Contact.Contact.Correspondence': {
   'Participant': 'Participant',
   'Place': 'Place',
   'Topic': 'Topic'
  },
  'Contact.Contact.Meet': {
   'Participant': 'Participant',
   'Place': 'Place',
   'Topic': 'Topic'
  },
  'Contact.Contact.Unspecified': {
   'Participant': 'Participant',
   'Place': 'Place',
   'Topic': 'Topic'
  },
  'Contact.RequestCommand.Broadcast': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient'
  },
  'Contact.RequestCommand.Correspondence': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient',
   'Topic': 'Topic'
  },
  'Contact.RequestCommand.Meet': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient'
  },
  'Contact.RequestCommand.Unspecified': {
   'Communicator': 'Communicator',
   'Place': 'Place',
   'Recipient': 'Recipient'
  },
  'Contact.ThreatenCoerce.Broadcast': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient'
  },
  'Contact.ThreatenCoerce.Correspondence': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient'
  },
  'Contact.ThreatenCoerce.Unspecified': {
   'Communicator': 'Communicator',
   'Recipient': 'Recipient'
  },
  'Control.ImpedeInterfereWith.Unspecified': {
   'Impeder': 'Impeder',
   'Place': 'Place'
  },
  'Disaster.Crash.Unspecified': {
   'CrashObject': 'Crash_Object',
   'Place': 'Place',
   'Vehicle': 'Vehicle'
  },
  'Disaster.DiseaseOutbreak.Unspecified': {
   'Place': 'Place',
   'Victim': 'Victim'
  },
  'GenericCrime.GenericCrime.GenericCrime': {
   'Perpetrator': 'Perpetrator',
   'Place': 'Place',
   'Victim': 'Victim'
  },
  'Justice.Acquit.Unspecified': {
   'Defendant': 'Defendant'
  },
  'Justice.ArrestJailDetain.Unspecified': {
   'Detainee': 'Detainee',
   'Jailer': 'Jailer',
   'Place': 'Place'
  },
  'Justice.ChargeIndict.Unspecified': {
   'Defendant': 'Defendant',
   'JudgeCourt': 'Judge_Court',
   'Place': 'Place',
   'Prosecutor': 'Prosecutor'
  },
  'Justice.Convict.Unspecified': {
   'Defendant': 'Defendant',
   'JudgeCourt': 'Judge_Court'
  },
  'Justice.InvestigateCrime.Unspecified': {
   'Defendant': 'Defendant',
   'Investigator': 'Investigator',
   'ObservedEntity': 'Observed_Entity',
   'Observer': 'Investigator',
   'Place': 'Place'
  },
  'Justice.ReleaseParole.Unspecified': {
   'Defendant': 'Defendant',
   'JudgeCourt': 'Judge_Court'
  },
  'Justice.Sentence.Unspecified': {
   'Defendant': 'Defendant',
   'JudgeCourt': 'Judge_Court',
   'Place': 'Place'
  },
  'Justice.TrialHearing.Unspecified': {
   'Defendant': 'Defendant',
   'JudgeCourt': 'Judge_Court',
   'Place': 'Place',
   'Prosecutor': 'Prosecutor'
  },
  'Life.Die.Unspecified': {
   'Killer': 'Killer',
   'Place': 'Place',
   'Victim': 'Victim'
  },
  'Life.Infect.Unspecified': {
   'Victim': 'Victim'
  },
  'Life.Injure.Unspecified': {
   'BodyPart': 'Body_Part',
   'Injurer': 'Injurer',
   'Instrument': 'Instrument',
   'Victim': 'Victim'
  },
  'Medical.Intervention.Unspecified': {
   'Patient': 'Patient',
   'Place': 'Place',
   'Treater': 'Treater'
  },
  'Movement.Transportation.Evacuation': {
   'Destination': 'Destination',
   'Origin': 'Origin',
   'PassengerArtifact': 'Passenger_Artifact',
   'Transporter': 'Transporter'
  },
  'Movement.Transportation.IllegalTransportation': {
   'Destination': 'Destination',
   'PassengerArtifact': 'Passenger_Artifact',
   'Transporter': 'Transporter',
   'Vehicle': 'Vehicle'
  },
  'Movement.Transportation.PreventPassage': {
   'Destination': 'Destination',
   'Origin': 'Origin',
   'PassengerArtifact': 'Passenger_Artifact',
   'Preventer': 'Preventer',
   'Transporter': 'Transporter',
   'Vehicle': 'Vehicle'
  },
  'Movement.Transportation.Unspecified': {
   'Destination': 'Destination',
   'Origin': 'Origin',
   'PassengerArtifact': 'Passenger_Artifact',
   'Transporter': 'Transporter',
   'Vehicle': 'Vehicle'
  },
  'Personnel.EndPosition.Unspecified': {
   'Employee': 'Employee',
   'PlaceOfEmployment': 'Place_Of_Employment'
  },
  'Personnel.StartPosition.Unspecified': {
   'Employee': 'Employee',
   'Place': 'Place_Of_Employment',
   'PlaceOfEmployment': 'Place_Of_Employment',
   'Position': 'Position'
  },
  'Transaction.Donation.Unspecified': {
   'ArtifactMoney': 'Payment_Barter',
   'Giver': 'Giver',
   'Recipient': 'Recipient'
  },
  'Transaction.ExchangeBuySell.Unspecified': {
   'AcquiredEntity': 'Acquired_Entity',
   'Giver': 'Giver',
   'PaymentBarter': 'Payment_Barter',
   'Recipient': 'Recipient'
  }
 }
}


original_to_new_argument_role_lookup_rams = {
 'rams': {
  **{
   evt: {
    'artifact': 'Artifact',
    'damager': 'Damager',
    'instrument': 'Instrument',
    'place': 'Place'
   }
   for evt in ['artifactexistence.damagedestroy.damage']
  },
  **{
   evt: {
    'artifact': 'Artifact',
    'destroyer': 'Destroyer',
    'instrument': 'Instrument',
    'place': 'Place'
   }
   for evt in ['artifactexistence.damagedestroy.destroy']
  },
  **{
   evt: {
    'artifact': 'Artifact',
    'damagerdestroyer': 'Damager',
    'instrument': 'Instrument',
    'place': 'Place'
   }
   for evt in ['artifactexistence.damagedestroy.n/a']
  },
  **{
   evt: {
    'attacker': 'Attacker',
    'instrument': 'Instrument',
    'place': 'Place',
    'target': 'Target'
   }
   for evt in [
    'conflict.attack.airstrikemissilestrike',
    'conflict.attack.biologicalchemicalpoisonattack',
    'conflict.attack.bombing',
    'conflict.attack.firearmattack',
    'conflict.attack.hanging',
    'conflict.attack.invade',
    'conflict.attack.n/a',
    'conflict.attack.selfdirectedbattle',
    'conflict.attack.setfire',
    'conflict.attack.stabbing',
    'conflict.attack.strangling'
   ]
  },
  'conflict.attack.stealrobhijack': {
   'artifact': 'Artifact',
   'attacker': 'Attacker',
   'instrument': 'Instrument',
   'place': 'Place',
   'target': 'Target'
  },
  **{
   evt: {
    'demonstrator': 'Demonstrator',
    'place': 'Place'
   }
   for evt in [
    'conflict.demonstrate.marchprotestpoliticalgathering',
    'conflict.demonstrate.n/a'
   ]
  },
  'conflict.yield.n/a': {
   'place': 'Place',
   'recipient': 'Recipient',
   'yielder': 'Surrenderer'
  },
  'conflict.yield.retreat': {
   'destination': 'Destination',
   'origin': 'Origin',
   'retreater': 'Retreater'
  },
  'conflict.yield.surrender': {
   'place': 'Place',
   'recipient': 'Recipient',
   'surrenderer': 'Surrenderer'
  },
  **{
   evt: {
    'participant': 'Participant',
    'place': 'Place'
   }
   for evt in [
    'contact.collaborate.correspondence',
    'contact.collaborate.meet',
    'contact.collaborate.n/a',
    'contact.discussion.correspondence',
    'contact.discussion.meet',
    'contact.discussion.n/a',
    'contact.negotiate.correspondence',
    'contact.negotiate.meet',
    'contact.negotiate.n/a'
   ]
  },
  **{
   evt: {
    'deceased': 'Deceased',
    'participant': 'Participant',
    'place': 'Place'
   }
   for evt in ['contact.funeralvigil.meet', 'contact.funeralvigil.n/a']
  },
  **{
   evt: {
    'communicator': 'Communicator',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in [
    'contact.commandorder.broadcast',
    'contact.commandorder.correspondence',
    'contact.commandorder.meet',
    'contact.commandorder.n/a',
    'contact.commitmentpromiseexpressintent.broadcast',
    'contact.commitmentpromiseexpressintent.correspondence',
    'contact.commitmentpromiseexpressintent.meet',
    'contact.commitmentpromiseexpressintent.n/a',
    'contact.requestadvise.broadcast',
    'contact.requestadvise.correspondence',
    'contact.requestadvise.meet',
    'contact.requestadvise.n/a'
   ]
  },
  **{
   evt: {
    'communicator': 'Communicator',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in [
    'contact.mediastatement.broadcast',
    'contact.mediastatement.n/a',
    'contact.publicstatementinperson.broadcast',
    'contact.publicstatementinperson.n/a'
   ]
  },
  **{
   evt: {
    'communicator': 'Communicator',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in [
    'contact.prevarication.broadcast',
    'contact.prevarication.correspondence',
    'contact.prevarication.meet',
    'contact.prevarication.n/a',
    'contact.threatencoerce.broadcast',
    'contact.threatencoerce.correspondence',
    'contact.threatencoerce.meet',
    'contact.threatencoerce.n/a'
   ]
  },
  'disaster.accidentcrash.accidentcrash': {
   'crashobject': 'Crash_Object',
   'driverpassenger': 'Driver_Passenger',
   'place': 'Place',
   'vehicle': 'Vehicle'
  },
  'disaster.fireexplosion.fireexplosion': {
   'fireexplosionobject': 'Fire_Explosion_Object',
   'instrument': 'Instrument',
   'place': 'Place'
  },
  **{
   evt: {
    'participant': 'Participant',
    'place': 'Place'
   }
   for evt in ['government.agreements.acceptagreementcontractceasefire', 'government.agreements.n/a']
  },
  'government.agreements.rejectnullifyagreementcontractceasefire': {
   'otherparticipant': 'Other_Participant',
   'place': 'Place',
   'rejecternullifier': 'Rejecter_Nullifier'
  },
  'government.agreements.violateagreement': {
   'otherparticipant': 'Other_Participant',
   'place': 'Place',
   'violator': 'Violator'
  },
  'government.formation.mergegpe': {
   'participant': 'Participant',
   'place': 'Place'
  },
  **{
   evt: {
    'founder': 'Founder',
    'gpe': 'Gpe',
    'place': 'Place'
   }
   for evt in ['government.formation.n/a', 'government.formation.startgpe']
  },
  'government.legislate.legislate': {
   'governmentbody': 'Government_Body',
   'law': 'Law',
   'place': 'Place'
  },
  'government.spy.spy': {
   'beneficiary': 'Beneficiary',
   'observedentity': 'Observed_Entity',
   'place': 'Place',
   'spy': 'Spy'
  },
  **{
   evt: {
    'ballot': 'Ballot',
    'candidate': 'Candidate',
    'place': 'Place',
    'result': 'Result',
    'voter': 'Voter'
   }
   for evt in ['government.vote.castvote', 'government.vote.n/a']
  },
  'government.vote.violationspreventvote': {
   'ballot': 'Ballot',
   'candidate': 'Candidate',
   'place': 'Place',
   'preventer': 'Preventer',
   'voter': 'Voter'
  },
  **{
   evt: {
    'inspectedentity': 'Inspected_Entity',
    'inspector': 'Inspector',
    'place': 'Place'
   }
   for evt in [
    'inspection.sensoryobserve.inspectpeopleorganization',
    'inspection.sensoryobserve.physicalinvestigateinspect'
   ]
  },
  'inspection.sensoryobserve.monitorelection': {
   'monitor': 'Observer',
   'monitoredentity': 'Monitored_Entity',
   'place': 'Place'
  },
  'inspection.sensoryobserve.n/a': {
   'observedentity': 'Observed_Entity',
   'observer': 'Observer',
   'place': 'Place'
  },
  'justice.arrestjaildetain.arrestjaildetain': {
   'crime': 'Crime',
   'detainee': 'Detainee',
   'jailer': 'Jailer',
   'place': 'Place'
  },
  **{
   evt: {
    'crime': 'Crime',
    'defendant': 'Defendant',
    'judgecourt': 'Judge_Court',
    'place': 'Place',
    'prosecutor': 'Prosecutor'
   }
   for evt in [
    'justice.initiatejudicialprocess.chargeindict',
    'justice.initiatejudicialprocess.n/a',
    'justice.initiatejudicialprocess.trialhearing'
   ]
  },
  'justice.investigate.investigatecrime': {
   'crime': 'Crime',
   'defendant': 'Defendant',
   'investigator': 'Investigator',
   'place': 'Place'
  },
  'justice.investigate.n/a': {
   'defendant': 'Defendant',
   'investigator': 'Investigator',
   'place': 'Place'
  },
  **{
   evt: {
    'crime': 'Crime',
    'defendant': 'Defendant',
    'judgecourt': 'Judge_Court',
    'place': 'Place'
   }
   for evt in ['justice.judicialconsequences.convict', 'justice.judicialconsequences.n/a']
  },
  'justice.judicialconsequences.execute': {
   'crime': 'Crime',
   'defendant': 'Defendant',
   'executioner': 'Executioner',
   'place': 'Place'
  },
  'justice.judicialconsequences.extradite': {
   'crime': 'Crime',
   'defendant': 'Defendant',
   'destination': 'Destination',
   'extraditer': 'Extraditer',
   'origin': 'Origin'
  },
  'life.die.deathcausedbyviolentevents': {
   'instrument': 'Instrument',
   'killer': 'Killer',
   'place': 'Place',
   'victim': 'Victim'
  },
  **{
   evt: {
    'place': 'Place',
    'victim': 'Victim'
   }
   for evt in ['life.die.n/a', 'life.die.nonviolentdeath']
  },
  **{
   evt: {
    'place': 'Place',
    'victim': 'Victim'
   }
   for evt in ['life.injure.illnessdegradationhungerthirst']
  },
  'life.injure.illnessdegradationphysical': {
   'victim': 'Victim'
  },
  'life.injure.injurycausedbyviolentevents': {
   'injurer': 'Injurer',
   'instrument': 'Instrument',
   'place': 'Place',
   'victim': 'Victim'
  },
  'life.injure.n/a': {
   'injurer': 'Injurer',
   'place': 'Place',
   'victim': 'Victim'
  },
  **{
   evt: {
    'artifact': 'Artifact',
    'instrument': 'Instrument',
    'manufacturer': 'Manufacturer',
    'place': 'Place'
   }
   for evt in [
    'manufacture.artifact.build',
    'manufacture.artifact.createintellectualproperty',
    'manufacture.artifact.createmanufacture',
    'manufacture.artifact.n/a'
   ]
  },
  **{
   evt: {
    'artifact': 'Artifact',
    'destination': 'Destination',
    'origin': 'Origin',
    'transporter': 'Transporter',
    'vehicle': 'Vehicle'
   }
   for evt in [
    'movement.transportartifact.bringcarryunload',
    'movement.transportartifact.disperseseparate',
    'movement.transportartifact.n/a',
    'movement.transportartifact.nonviolentthrowlaunch',
    'movement.transportartifact.receiveimport',
    'movement.transportartifact.sendsupplyexport',
    'movement.transportartifact.smuggleextract'
   ]
  },
  'movement.transportartifact.fall': {
   'artifact': 'Artifact',
   'destination': 'Destination',
   'origin': 'Origin'
  },
  'movement.transportartifact.grantentry': {
   'artifact': 'Artifact',
   'destination': 'Destination',
   'origin': 'Origin',
   'transporter': 'Transporter'
  },
  'movement.transportartifact.hide': {
   'artifact': 'Artifact',
   'hidingplace': 'Hiding_Place',
   'origin': 'Origin',
   'transporter': 'Transporter',
   'vehicle': 'Vehicle'
  },
  **{
   evt: {
    'artifact': 'Artifact',
    'destination': 'Destination',
    'origin': 'Origin',
    'preventer': 'Preventer',
    'transporter': 'Transporter'
   }
   for evt in ['movement.transportartifact.prevententry', 'movement.transportartifact.preventexit']
  },
  **{
   evt: {
    'destination': 'Destination',
    'origin': 'Origin',
    'passenger': 'Passenger',
    'transporter': 'Transporter',
    'vehicle': 'Vehicle'
   }
   for evt in [
    'movement.transportperson.bringcarryunload',
    'movement.transportperson.disperseseparate',
    'movement.transportperson.evacuationrescue',
    'movement.transportperson.n/a',
    'movement.transportperson.smuggleextract'
   ]
  },
  'movement.transportperson.fall': {
   'destination': 'Destination',
   'origin': 'Origin',
   'passenger': 'Passenger'
  },
  'movement.transportperson.grantentryasylum': {
   'destination': 'Destination',
   'granter': 'Granter',
   'origin': 'Origin',
   'passenger': 'Passenger',
   'transporter': 'Transporter'
  },
  'movement.transportperson.hide': {
   'hidingplace': 'Hiding_Place',
   'origin': 'Origin',
   'passenger': 'Passenger',
   'transporter': 'Transporter',
   'vehicle': 'Vehicle'
  },
  **{
   evt: {
    'destination': 'Destination',
    'origin': 'Origin',
    'passenger': 'Passenger',
    'preventer': 'Preventer',
    'transporter': 'Transporter'
   }
   for evt in ['movement.transportperson.prevententry', 'movement.transportperson.preventexit']
  },
  'movement.transportperson.selfmotion': {
   'destination': 'Destination',
   'origin': 'Origin',
   'transporter': 'Transporter'
  },
  **{
   evt: {
    'candidate': 'Candidate',
    'place': 'Place',
    'voter': 'Voter'
   }
   for evt in ['personnel.elect.n/a', 'personnel.elect.winelection']
  },
  **{
   evt: {
    'employee': 'Employee',
    'place': 'Place_Of_Employment',
    'placeofemployment': 'Place_Of_Employment'
   }
   for evt in [
    'personnel.endposition.firinglayoff',
    'personnel.endposition.n/a',
    'personnel.endposition.quitretire',
    'personnel.startposition.hiring',
    'personnel.startposition.n/a'
   ]
  },
  'transaction.transaction.embargosanction': {
   'artifactmoney': 'Payment_Barter',
   'giver': 'Giver',
   'place': 'Place',
   'preventer': 'Preventer',
   'recipient': 'Recipient'
  },
  **{
   evt: {
    'beneficiary': 'Beneficiary',
    'giver': 'Giver',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in ['transaction.transaction.giftgrantprovideaid']
  },
  'transaction.transaction.n/a': {
   'beneficiary': 'Beneficiary',
   'participant': 'Recipient',
   'place': 'Place'
  },
  'transaction.transaction.transfercontrol': {
   'beneficiary': 'Beneficiary',
   'giver': 'Giver',
   'place': 'Place',
   'recipient': 'Recipient',
   'territoryorfacility': 'Territoryor_Facility'
  },
  **{
   evt: {
    'beneficiary': 'Beneficiary',
    'giver': 'Giver',
    'money': 'Money',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in [
    'transaction.transfermoney.borrowlend',
    'transaction.transfermoney.giftgrantprovideaid',
    'transaction.transfermoney.n/a',
    'transaction.transfermoney.payforservice',
    'transaction.transfermoney.purchase'
   ]
  },
  'transaction.transfermoney.embargosanction': {
   'giver': 'Giver',
   'money': 'Money',
   'place': 'Place',
   'preventer': 'Preventer',
   'recipient': 'Recipient'
  },
  **{
   evt: {
    'artifact': 'Acquired_Entity',
    'beneficiary': 'Beneficiary',
    'giver': 'Giver',
    'place': 'Place',
    'recipient': 'Recipient'
   }
   for evt in [
    'transaction.transferownership.borrowlend',
    'transaction.transferownership.giftgrantprovideaid',
    'transaction.transferownership.n/a',
    'transaction.transferownership.purchase'
   ]
  },
  'transaction.transferownership.embargosanction': {
   'artifact': 'Acquired_Entity',
   'giver': 'Giver',
   'place': 'Place',
   'preventer': 'Preventer',
   'recipient': 'Recipient'
  }
 }
}

# Dataset-wise lookup from original argument role to refined unified role.
original_to_new_argument_role_lookup_by_dataset = {"m2e2": original_to_new_argument_role_lookup_m2e2['m2e2'],
 "wikievents": original_to_new_argument_role_lookup_wikievents['wikievents'], 
 "rams": original_to_new_argument_role_lookup_rams['rams']}






