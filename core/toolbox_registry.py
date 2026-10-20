"""Versioned, extensible structured worksheets. Guidance is concise original wording.

Sources checked 2026-10-14. Schemas describe operational worksheets, not official
CEVA method approvals. Each method exports full JSON/CSV and a generated view.
"""
from copy import deepcopy
from uuid import uuid4

ASQ='https://asq.org/quality-resources/'
LEI='https://www.lean.org/lexicon-terms/'

def fields(text):
    # key:label:type:choices; numeric cells remain blank until supplied.
    result=[]
    for part in text.split('|'):
        bits=part.split(':');key=bits[0]
        result.append({'key':key,'label':bits[1] if len(bits)>1 and bits[1] else key.replace('_',' ').capitalize(),
                       'type':bits[2] if len(bits)>2 else 'text','choices':bits[3].split(',') if len(bits)>3 else []})
    return result

REGISTRY={}
def method(key,name,goal,stage,kind,rows,source,purpose,steps,pitfall,example,*,meta='',visual='cards',difficulty='basic',data='observations',defaults=None):
    REGISTRY[key]={'key':key,'name':name,'version':1,'goal':goal,'stage':stage,'kind':kind,'fields':fields(rows),
        'meta':fields(meta),'source':source,'purpose':purpose,'when':purpose,'steps':steps.split('|'),'pitfall':pitfall,
        'example':'Fictional logistics example: '+example,'visual':visual,'difficulty':difficulty,'data_need':data,
        'defaults':defaults or [],'exports':['JSON','CSV','SVG','A3']}

method('5w2h','5W2H','Define','Plan','analysis',
       'question:Question:select:Who,What,When,Where,Why,How,How much|answer:Observed answer|source:Basis / source',ASQ+'problem-solving',
       'Clarify an insufficiently defined problem.','State the issue|Answer each question from facts|List remaining uncertainties',
       'An answer is not a verified cause.','Clarify where picking errors occur.',defaults=[{'question':s} for s in ['Who','What','When','Where','Why','How','How much']])
method('is-not','Is / Is Not','Define','Plan','analysis',
       'dimension:Dimension|is:Observed IS|is_not:Observed IS NOT|difference:Relevant difference|test:Testable explanation',ASQ+'problem-solving',
       'Compare affected and unaffected situations.','Set boundaries|Compare like conditions|Test a distinguishing factor',
       'Differences suggest tests, not causality.','Compare errors on two pick lanes.')
method('gemba','Gemba observation','Define','Plan','practice',
       'location:Process / place|time:Observed at|standard:Expected standard|observed:Actual observation|question:Question for team|follow_up:Follow-up',LEI+'gemba/',
       'Understand work at the place it happens.','Observe respectfully|Compare actual work with standard|Agree a follow-up',
       'Do not turn observation into blame.','Observe a pallet handoff.')
method('voc','Voice of Customer / CTQ','Define','Plan','analysis',
       'voice:Customer statement|context:Source / context|need:Underlying need|ctq:Observable CTQ|criterion:Acceptance criterion|unit:Unit',ASQ+'voice-of-the-customer',
       'Translate customer needs into checkable conditions.','Capture the voice|Clarify the need|Agree an operational criterion',
       'Confirm the translation with the customer.','Translate on-time delivery into a defined cut-off measure.')
method('sipoc','SIPOC','Define','Plan','analysis',
       'supplier:Supplier|input:Input|process:Process step|output:Output|customer:Customer|requirement:Output requirement',ASQ+'sipoc',
       'Set high-level process boundaries and handoffs.','Define start and end|Map inputs and outputs|Confirm requirements with customers',
       'A high-level map omits operational detail.','Map receipt-to-putaway.',visual='flow')
method('ishikawa','Ishikawa / fishbone','Causes','Plan','analysis',
       'category:Category|cause:Possible cause|parent:Parent row ID (subcause)|state:Cause status:select:hypothesis,validated|evidence_id:Evidence ID|test:Validation / uncertainty',ASQ+'fishbone',
       'Organize possible causes of a defined effect.','Agree the effect|Add categories, causes and subcauses|Test hypotheses against evidence',
       'The diagram does not prove root causes.','Explore damage during outbound handling.',
       meta='effect:Problem / effect|categories:Categories (one per line):textarea',visual='fishbone',defaults=[],data='hypotheses')
method('5whys','5 Whys','Causes','Plan','analysis',
       'branch:Chain / branch|parent:Parent row ID|question:Why question|answer:Answer / hypothesis|uncertainty:Uncertainty|countermeasure:Proposed countermeasure|state:Cause status:select:hypothesis,validated|evidence_id:Evidence ID',LEI+'5-whys/',
       'Trace a gap beyond its immediate symptom.','Ask why from facts|Branch where explanations differ|Test the answer before acting',
       'Five is a starting aid, not a required endpoint.','Trace recurring label reprints.',visual='tree',defaults=[{'branch':'Main','question':'Why?','state':'hypothesis'} for _ in range(5)],data='hypotheses')
method('brainstorm','Brainstorming','Ideas','Plan','analysis',
       'idea:Idea|contributor:Contributor / team alias|origin:Observation / origin|label:Label|test:Possible test',ASQ+'brainstorming',
       'Generate options before selecting a solution.','Frame the question|Record ideas without judging|Evaluate separately',
       'Popularity is not evidence.','Collect ideas to reduce scanner searching.')
method('affinity','Affinity diagram','Ideas','Plan','analysis',
       'card:Idea / observation|group:Group (blank = ungrouped)|label:Label|origin:Origin',ASQ+'affinity',
       'Group many observations by related themes.','Capture separate cards|Name groups|Move cards and discuss differences',
       'Grouping demonstrates similarity, not causality.','Group picking feedback by theme.',meta='groups:Named groups (one per line):textarea',visual='affinity')
method('relations','Relations diagram','Causes','Plan','analysis',
       'from:From factor|to:To factor|relationship:Proposed influence|evidence_id:Evidence ID|uncertainty:Uncertainty',ASQ+'relations-diagram',
       'Explore dependencies between interacting factors.','List factors|Draw directed relationships|Check high-influence hypotheses',
       'An arrow alone does not establish cause.','Explore workload and rework dependencies.',visual='relations')
method('tree','Tree diagram','Ideas','Plan','analysis',
       'node:Node / objective|parent:Parent row ID|type:Node type:select:objective,means,test|criterion:Completion criterion|owner:Owner',ASQ+'tree-diagram',
       'Break a broad objective into workable parts.','State the objective|Decompose means|Check coverage and assign owners',
       'Hierarchy is a planning structure.','Break damage reduction into tests.',visual='tree')
method('flowchart','Flowchart / swimlane','Process','Plan','analysis',
       'step:Step / decision|lane:Lane / owner|next:Next row IDs (comma-separated)|state:Process state:select:current,future|type:Shape:select:process,decision,start,end|time:Duration:number|unit:Time unit|source:Measure source',ASQ+'flowchart',
       'Understand sequence, decisions and responsibility.','Observe the process|Map steps and decision branches|Compare a proposed future flow',
       'Measure times; a map is not a simulation.','Map goods receipt across roles.',visual='flow')
method('vsm','Current / future value-stream map','Process','Plan','analysis',
       'step:Process step|state:State:select:current,future|cycle:Cycle time:number|wait:Waiting time:number|wip:Work in process:number|information:Information / pull signal|unit:Time unit|source:Measure source',LEI+'value-stream-mapping/',
       'See material and information flow across a stream.','Record current flow and delays|Design a future state|Plan tests of the changes',
       'Same-unit sums are descriptive; do not imply a validated future state.','Map inbound pallets to available stock.',visual='vsm',difficulty='intermediate')
method('spaghetti','Spaghetti diagram','Process','Plan','analysis',
       'route:Route / operator alias|state:State:select:current,future|point:Location|x:X coordinate:number|y:Y coordinate:number|unit:Distance unit|source:Measurement source',ASQ+'spaghetti-diagram',
       'Expose walking or movement paths.','Define a measured coordinate scale|Record successive points|Compare actual and proposed routes',
       'Straight segments approximate distance; obstacles and routes need observation.','Trace a picker collecting packaging.',visual='spaghetti')
method('waste','Waste analysis','Process','Plan','analysis',
       'category:Waste category|observation:Observed waste|time:Measured duration:number|unit:Unit|source:Source|action:Proposed change|owner:Owner',LEI+'waste/',
       'Identify activities consuming resources without customer value.','Define local categories|Observe work|Select a change to test',
       'Required safety or compliance work cannot be removed by labeling it waste.','Record waiting at a loading dock.',meta='categories:Local waste categories (one per line):textarea')
method('check-sheet','Check sheet / tally','Data','Check','analysis',
       'category:Operationally defined category|period:Date / interval|count:Count:number|location:Location / population|source:Observer / source',ASQ+'check-sheet',
       'Collect repeatable event counts.','Define each category|Trial the sheet|Record observations consistently',
       'Changing definitions invalidates comparisons.','Count damaged cartons by shift.',visual='bars',data='counts')
method('pareto','Pareto','Data','Check','analysis',
       'category:Category|value:Frequency / cost / time:number|unit:Unit|source:Data source',ASQ+'pareto',
       'Prioritize measured categories by contribution.','Choose one metric and unit|Aggregate categories and sort descending|Inspect cumulative shares',
       'The 80% line is a reference, not a guaranteed 80/20 law.','Compare picking error counts by type.',
       meta='metric:Metric:select:frequency,cost,time|unit:Selected unit|aggregation:Aggregation:select:sum',visual='pareto',data='counts')
method('stratification','Stratification','Data','Check','analysis',
       'stratum:Group / source|value:Observed value:number|unit:Unit|period:Measurement period|population:Population|source:Source',ASQ+'stratification',
       'Compare data from distinct operational groups.','Define groups before analysis|Use comparable observations|Compare group distributions',
       'Group differences do not explain their cause.','Compare pick duration by zone.',visual='bars',data='numeric')
method('histogram','Histogram','Data','Check','analysis',
       'value:Numeric observation:number|unit:Unit|period:Measurement period|source:Source',ASQ+'histogram',
       'Inspect the distribution of numeric data.','Collect representative measurements|Choose equal-width bins|Inspect shape and sample size',
       'Small samples and chosen bins can mislead; no normality claim.','Inspect loading duration.',meta='bins:Number of equal-width bins:number|unit:Selected unit',visual='histogram',data='numeric')
method('scatter','Scatterplot','Data','Check','analysis',
       'x:X observation:number|y:Y observation:number|x_unit:X unit|y_unit:Y unit|period:Paired observation period|source:Source',ASQ+'scatter-diagram',
       'Explore association between paired numeric measures.','Pair observations correctly|Plot both measures|Investigate alternative explanations',
       'Correlation does not establish causality.','Compare queue length and waiting time.',visual='scatter',data='paired numeric')
method('run-chart','Run chart','Data','Check','analysis',
       'period:Ordered measurement time|value:Value:number|unit:Unit|source:Source',ASQ+'seven-basic-quality-tools',
       'See how a measure changes over time.','Record observations in time order|Plot values and median|Investigate visible changes',
       'This plot makes no automatic special-cause significance claim.','Track daily dispatch delays.',visual='run',data='time series')
method('control-chart','Control chart (I–MR)','Data','Check','analysis',
       'period:Ordered measurement time|value:Individual continuous observation:number|unit:Unit|source:Source',ASQ+'control-chart',
       'Explore continuous individual observations using I–MR limits.','Collect a stable consecutive baseline|Estimate moving-range limits|Investigate out-of-limit points',
       'Limits are estimated process variation, not targets/specifications. Only I–MR is implemented; no attribute/subgroup charts.','Inspect consecutive carton-weight observations.',visual='control',data='time series',difficulty='advanced')
method('boxplot','Boxplot','Data','Check','analysis',
       'group:Comparable group|value:Observation:number|unit:Unit|period:Measurement period|source:Source',ASQ+'box-whisker-plot',
       'Compare median, quartiles and spread across groups.','Define comparable groups|Collect numeric values|Inspect quartiles and outliers',
       'Tukey whiskers and linear-interpolation quartiles are descriptive.','Compare unloading duration across shifts.',visual='boxplot',data='numeric')
method('impact-effort','Impact / effort matrix','Choose','Do','analysis',
       'option:Option|impact:Local impact 1–5:number|effort:Local effort 1–5:number|basis:Scoring basis|risk:Risk / condition',ASQ+'impact-effort-matrix',
       'Discuss practical options against impact and effort.','Define the local 1–5 anchors|Score options|Discuss risks before selection',
       'Local scores are subjective and not CEVA policy.','Compare scanner placement options.',meta='scale:Local scoring anchors',visual='matrix')
method('decision-matrix','Weighted decision matrix','Choose','Do','analysis',
       'option:Option|criterion:Criterion|weight:Nonnegative weight:number|score:Score on defined local scale:number|basis:Score basis',ASQ+'decision-matrix',
       'Compare options using explicit weighted criteria.','Agree criteria, weights and scale|Score every option consistently|Inspect sensitivity and assumptions',
       'Weights and scores require judgment; missing criteria block ranking.','Compare two packaging systems.',meta='scale:Local score definition',visual='bars',difficulty='intermediate')
method('fmea','FMEA','Risk','Do','analysis',
       'process:Process / function|failure:Failure mode|effect:Effect|cause:Potential cause|control:Current control|severity:Severity 1–10:number|occurrence:Occurrence 1–10:number|detection:Detection 1–10:number|action:Action|owner:Owner',ASQ+'fmea',
       'Examine failure modes and planned controls.','Define the local rating anchors|Assess effects and controls|Assign mitigation and reassess',
       'RPN is only a local screening aid; high severity needs attention regardless of RPN.','Review wrong-item shipment failure modes.',meta='scale:Local severity / occurrence / detection anchors',visual='bars',difficulty='advanced')
method('poka-yoke','Poka-Yoke','Risk','Do','practice',
       'error:Potential error|mechanism:Prevention / detection mechanism|test:Challenge test|failure_response:Response when test fails|owner:Owner|result:Observed test result',LEI+'poka-yoke/',
       'Prevent errors or make them immediately detectable.','Define the error|Design a prevention or detection test|Check failure response and maintenance',
       'A reminder alone is not proven error prevention.','Test a barcode mismatch interlock.')
method('5s','5S','Workplace','Do','practice',
       'pillar:5S component:select:Sort,Set in order,Shine,Standardize,Sustain|observation:Observation|before_attachment:Before photo attachment ID|after_attachment:After photo attachment ID|action:Action|owner:Owner|follow_up:Follow-up date|score:Local score 0–2:number',LEI+'five-s/',
       'Build a workplace standard that makes problems visible.','Observe each of the five components|Agree changes and photo evidence|Schedule sustain checks',
       'Local 0 = absent, 1 = partly demonstrated, 2 = demonstrated; not a TCA classification.','Organize the packing station and check sustain.',visual='5s',defaults=[{'pillar':s} for s in ['Sort','Set in order','Shine','Standardize','Sustain']])
method('red-tag','Red-tag register','Workplace','Do','practice',
       'item:Tagged item|location:Location|reason:Reason|tag_date:Tag date|owner:Decision owner|disposition:Decision / disposition|follow_up:Follow-up',LEI+'five-s/',
       'Track decisions on unnecessary workplace items.','Tag with context|Agree a disposition|Record the outcome',
       'Do not dispose of safety/compliance assets without authority.','Review unused packaging fixtures.')
method('visual-management','Visual-management standard','Workplace','Act','practice',
       'location:Point of use|standard:Normal condition|signal:Abnormal signal|response:Required response|owner:Owner|frequency:Review frequency|check:Latest check', 'https://www.lean.org/the-lean-post/articles/reinforcing-lean-behavior-through-visual-management/',
       'Make normal and abnormal conditions actionable.','Define the standard|Place a visible signal|Test the response',
       'A board without a response routine does not improve performance.','Show the dock queue and escalation owner.')
method('kanban','Kanban / pull / WIP','Flow','Do','practice',
       'lane:Process / lane|signal:Replenishment signal|wip:Current WIP:number|limit:Local WIP limit:number|unit:Item unit|replenishment:Replenishment response|owner:Owner',LEI+'kanban/',
       'Control work release through explicit downstream demand.','Define the pull signal|Set and test local WIP limits|Respond to blocked flow',
       'A board alone does not create pull; limits are local experiments.','Test replenishment signals for cartons.',visual='bars')
method('takt','Takt / cycle-time analysis','Flow','Check','analysis',
       'process:Process|cycle:Observed cycle time:number|unit:Time unit|source:Measurement source|period:Period',LEI+'takt-time/',
       'Compare actual cycle times with customer demand pace.','Define net available time and demand for the same period|Measure cycle time|Inspect the gap',
       'Demand must be positive; all times must share the selected unit.','Compare packing cycles with shift demand.',meta='available:Net available time:number|demand:Customer demand units:number|unit:Time unit|period:Demand period',visual='takt',data='operational numeric')
method('yamazumi','Yamazumi / work balancing','Flow','Do','analysis',
       'operator:Station / operator alias|element:Work element|time:Duration:number|kind:Work kind:select:manual,walk,machine|unit:Time unit|source:Measure source',LEI+'operator-balance-chart/',
       'Balance work elements relative to takt.','Observe elements|Stack times per station|Test a safe redistribution',
       'Summed elements assume sequential work; overlap requires separate analysis.','Balance tasks across two pack stations.',meta='takt:Reference takt:number|unit:Time unit',visual='yamazumi',data='operational numeric')
method('smed','SMED','Flow','Do','practice',
       'element:Changeover element|kind:Current classification:select:internal,external|future_kind:Proposed classification:select:internal,external|before:Current duration:number|after:Proposed duration:number|unit:Time unit|test:Conversion test|owner:Owner',LEI+'single-minute-exchange-of-die/',
       'Reduce changeover by separating internal and external work.','Observe the changeover|Separate work needing a stop|Test safe conversion and simplify',
       'A proposed duration is not a realized saving.','Move label preparation outside a line stop.',visual='bars')
method('heijunka','Heijunka worksheet','Flow','Do','practice',
       'slot:Time slot|product:Product / service family|quantity:Planned quantity:number|unit:Unit|demand:Demand basis|capacity:Capacity constraint',LEI+'heijunka/',
       'Plan a leveled mix and volume over time.','Define demand and capacity|Allocate a repeatable mix|Test stability and adjust',
       'A level plan needs stable capability and cannot erase demand variability.','Plan a repeatable outbound service mix.',visual='heijunka')
method('standard-work','Standard work','Sustain','Act','practice',
       'step:Sequence step|time:Observed duration:number|unit:Time unit|wip:Standard WIP:number|key_point:Safety / quality key point|check:Verification|owner:Owner',LEI+'standardized-work/',
       'Describe the best current agreed work sequence.','Observe work and takt|Agree sequence and WIP|Train, verify and improve',
       'A document alone does not demonstrate adoption.','Agree a repeatable label-check sequence.',meta='takt:Reference takt|version:Local standard version',visual='flow')
method('twi','TWI job instruction','Sustain','Act','practice',
       'step:Important step|key_point:Key point|reason:Reason for key point|trainer:Trainer alias|practice:Try-out result|follow_up:Follow-up',LEI+'training-within-industry-twi/',
       'Teach a job consistently and safely.','Prepare the learner|Demonstrate and practice steps with key points and reasons|Follow up until competence is shown',
       'Attendance alone is not competence.','Teach pallet wrapping at point of use.',visual='flow')
method('control-plan','Control / sustain plan','Sustain','Act','practice',
       'characteristic:Controlled characteristic|standard:Expected standard|method:Check method|frequency:Frequency|owner:Owner|reaction:Reaction plan|next_check:Next check date|result:Observed check result',ASQ+'control-chart',
       'Keep a proven change effective over time.','Define the standard and check|Assign owner and frequency|Test the reaction plan',
       'This is an operational plan, not a statistical control-limit calculation.','Check barcode scan adherence.')
method('leader-work','Leader standard work','Sustain','Act','practice',
       'routine:Routine|location:Location|frequency:Frequency|standard:Expected behavior|owner:Owner|finding:Observed finding|follow_up:Follow-up',LEI+'leader-standard-work/',
       'Support improvement through a repeatable leadership routine.','Agree purposeful observations|Coach at the workplace|Follow up learning and blockers',
       'Checking a box does not establish capability.','Review the daily dock handoff.')
method('kamishibai','Kamishibai checks','Sustain','Act','practice',
       'card:Check card|standard:Standard to observe|due:Due date|owner:Owner|status:Result:select:pending,met,gap|finding:Observation|response:Response',LEI+'kamishibai-board/',
       'Rotate visible checks of agreed work standards.','Define cards and schedule|Observe the work|Respond to gaps',
       'A green card needs an actual observation.','Check a sample of dispatch handoffs.',visual='affinity')
method('kata','Toyota Kata experiment','Sustain','Act','approach',
       'target_condition:Target condition|obstacle:Current obstacle|experiment:Next experiment|prediction:Prediction|actual:Observed outcome|learning:Learning|next_step:Next step|check_date:Check date','https://www.lean.org/the-lean-post/articles/three-faces-of-lean-management/',
       'Learn toward a target condition through small experiments.','Choose one obstacle|State a prediction and test|Compare outcome and decide the next step',
       'Do not rewrite a prediction after seeing the result.','Test a different pick-route sequence.')
method('oee','TPM / OEE','Flow','Check','practice',
       'asset:Asset|planned:Planned production time:number|run:Run time:number|ideal_cycle:Ideal cycle time per unit:number|total:Total units:number|good:Good units:number|unit:Time unit|period:Measurement period|source:Source|maintenance:Maintenance / loss action',LEI+'overall-equipment-effectiveness/',
       'Separate availability, performance and quality losses.','Define scheduled time and ideal cycle|Measure downtime and output|Use loss evidence to plan TPM work',
       'Use the same time unit; invalid speed/output relationships are flagged, not capped.','Measure conveyor availability and defects.',visual='oee',data='operational numeric')
method('dmaic','DMAIC guidance','Approach','Plan','approach',
       'step:DMAIC phase:select:Define,Measure,Analyze,Improve,Control|decision:Decision / question|event_field:Existing PDCA field reference|worksheet_id:Existing worksheet ID|next:Next check',ASQ+'dmaic',
       'Guide a data-based improvement within this PDCA event.','Map phases to existing event data|Check the evidence at each decision|Keep one dossier',
       'Guidance references the same event; it does not certify Six Sigma completion.','Guide a recurring dispatch-delay investigation.',defaults=[{'step':s,'event_field':f} for s,f in [('Define','overall_problem'),('Measure','baseline'),('Analyze','root_cause'),('Improve','solution'),('Control','sustain')]],visual='flow',difficulty='advanced')
method('8d','8D guidance','Approach','Plan','approach',
       'step:Discipline:select:D1 Team,D2 Problem,D3 Containment,D4 Causes,D5 Corrective action,D6 Validate,D7 Prevent recurrence,D8 Recognize|decision:Decision / record|event_field:Existing PDCA field reference|worksheet_id:Existing worksheet ID|check:Evidence / follow-up',ASQ+'eight-disciplines-8d',
       'Guide containment and corrective action in the existing event.','Map disciplines to current records|Validate corrective action|Check recurrence controls',
       'Containment and permanent correction differ; no duplicate event dossier.','Guide an incorrect-shipment corrective action.',defaults=[{'step':s} for s in ['D1 Team','D2 Problem','D3 Containment','D4 Causes','D5 Corrective action','D6 Validate','D7 Prevent recurrence','D8 Recognize']],visual='flow',difficulty='advanced')
method('doe','DOE experiment planning','Approach','Plan','analysis',
       'run:Planned run / random order|factor_a:Factor A setting|factor_b:Factor B setting|block:Block / nuisance condition|replicate:Replicate|response:Response measure / unit|result:Observed response:number|safety:Safety / stopping rule',ASQ+'design-of-experiments',
       'Plan controlled trials of factors and interactions.','Define factors, ranges and safety|Plan randomization, blocks and repeats|Record responses for qualified analysis',
       'Planning only: no automatic significance, causal or optimum conclusion.','Plan safe packaging trials with two controlled factors.',meta='objective:Trial objective|randomization:Randomization plan|period:Trial period',difficulty='advanced')

DEFAULT_CATEGORIES='People\nMethod\nMaterial\nEquipment / machines\nMeasurement\nEnvironment'
def initial_payload(key,event=None):
    spec=REGISTRY[key]
    rows=deepcopy(spec['defaults'])
    for row in rows: row.update(id=str(uuid4()),archived=False)
    meta={'effect':event.data.get('overall_problem',event.title) if event else '',
          'categories':DEFAULT_CATEGORIES} if key=='ishikawa' else {}
    if key=='5w2h' and event:
        existing={'What':event.data.get('overall_problem',''),'Where':event.data.get('process_location',''),'Who':event.data.get('owner','')}
        for row in rows: row['answer']=existing.get(row['question'],'')
    return {'meta':meta,'rows':rows,'conclusion':'','links':{'actions':[],'observations':[],'evidence':[]},'include_in_a3':True}

# Explicit schema migrations: unsupported future versions fail rather than losing data.
SCHEMA_MIGRATIONS={}
def migrate_payload(method_key,payload,from_version,to_version):
    result=deepcopy(payload)
    for version in range(from_version,to_version):
        migration=SCHEMA_MIGRATIONS.get((method_key,version,version+1))
        if not migration: raise ValueError('No registered schema migration for this worksheet version.')
        result=migration(result)
    if from_version>to_version: raise ValueError('Schema downgrades are not supported.')
    return result
