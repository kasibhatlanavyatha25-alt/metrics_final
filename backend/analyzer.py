import os
import shutil
import tempfile
import datetime
from typing import Dict, List, Any, Optional, Callable
from sqlalchemy.orm import Session

from backend.models import (
    Project, Version, Commit, ClassMetric, ProjectMetric, 
    EvolutionMetric, DNAProfile, Mutation, ESDIResult, 
    RiskScore, Recommendation, Prediction, AnalysisRun
)
from backend.repo_manager import RepoManager
from backend.ck_extractor import analyze_java_repository
from backend.app.core.analyzer_adapters import default_registry
from backend.dna_engine import EvolutionaryDNAEngine
from backend.mutation_analyzer import MutationAnalyzer
from backend.esdi_engine import ESDIEngine
from backend.module_risk_engine import ModuleRiskEngine
from backend.recommendation_engine import RecommendationEngine
from backend.prediction_engine import QualityPredictionEngine

STAGES = [
    (1, "Repository validation"),
    (2, "Multi-language source detection"),
    (3, "Git history extraction"),
    (4, "Version identification"),
    (5, "Version checkout"),
    (6, "Unified metric extraction"),
    (7, "Historical dataset construction"),
    (8, "Evolutionary DNA generation"),
    (9, "Mutation analysis"),
    (10, "ESDI calculation"),
    (11, "Module risk analysis"),
    (12, "Recommendation generation"),
    (13, "Future prediction"),
    (14, "Report generation & persistence")
]

class RepositoryAnalyzer:
    def __init__(self, db: Session, repo_url_or_path: str, custom_weights: Optional[Dict[str, float]] = None):
        self.db = db
        self.input_target = repo_url_or_path.strip()
        self.custom_weights = custom_weights
        self.repo_manager = RepoManager(self.input_target)
        self.run_record: Optional[AnalysisRun] = None
        self.project_record: Optional[Project] = None

    def log_stage(self, stage_idx: int, message: str):
        stage_name = STAGES[stage_idx - 1][1] if 1 <= stage_idx <= len(STAGES) else f"Stage {stage_idx}"
        timestamp = datetime.datetime.utcnow().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [Stage {stage_idx}/14 - {stage_name}] {message}"
        print(log_entry)
        
        if self.run_record:
            self.run_record.current_stage = stage_name
            self.run_record.stage_index = stage_idx
            if self.run_record.logs is None:
                self.run_record.logs = []
            # Append new log
            logs_copy = list(self.run_record.logs)
            logs_copy.append(log_entry)
            self.run_record.logs = logs_copy
            self.db.commit()

    def run_full_analysis_existing(self) -> Dict[str, Any]:
        return self._execute_analysis_pipeline()

    def run_full_analysis(self) -> Dict[str, Any]:
        """Executes all 14 stages on real repository data."""
        # Pre-create project and run record if not already assigned
        if not self.project_record:
            self.project_record = Project(
                name="Analyzing...",
                repo_url=self.input_target if self.repo_manager.is_remote else None,
                local_path=self.input_target if not self.repo_manager.is_remote else None,
                language="Java"
            )
            self.db.add(self.project_record)
            self.db.flush()

        if not self.run_record:
            self.run_record = AnalysisRun(
                project_id=self.project_record.id,
                status="RUNNING",
                current_stage="Repository validation",
                stage_index=1,
                total_stages=14,
                logs=[]
            )
            self.db.add(self.run_record)
            self.db.commit()

        return self._execute_analysis_pipeline()

    def _execute_analysis_pipeline(self) -> Dict[str, Any]:
        try:
            # Stage 1: Repository validation
            self.log_stage(1, f"Validating repository source: {self.input_target}")
            validation = self.repo_manager.validate_repository()
            if not validation["is_valid"]:
                raise ValueError(validation["error_reason"])

            self.project_record.name = validation["repo_name"]
            self.project_record.language = validation.get("primary_language", "Multi-Language")
            self.project_record.first_commit_date = validation["first_commit_date"]
            self.project_record.latest_commit_date = validation["latest_commit_date"]
            self.project_record.total_commits = validation["total_commits"]
            self.project_record.total_java_files = validation.get("analyzable_files_count", validation.get("total_java_files", 0))
            self.db.commit()
            self.log_stage(1, f"Validation passed. Found {validation['total_commits']} commits. Languages: {list(validation.get('detected_languages', {}).keys())}")

            # Check if analyzable files exist
            if not validation.get("has_analyzable_files", False):
                warn_msg = validation.get("warning_message") or "Repository validated successfully, but no compatible analyzer is currently available for this language."
                raise ValueError(warn_msg)

            # Stage 2: Multi-language source detection
            analyzers_str = ", ".join(validation.get("supported_analyzers", ["Generic"]))
            self.log_stage(2, f"Discovered {validation['analyzable_files_count']} analyzable source files. Active Analyzers: [{analyzers_str}]. Sample: {', '.join(validation['sample_classes'][:3])}")

            # Stage 3: Git history extraction
            self.log_stage(3, f"Extracting full commit timeline from {validation['first_commit_date'].strftime('%Y-%m-%d')} to {validation['latest_commit_date'].strftime('%Y-%m-%d')}.")

            # Stage 4: Version identification
            self.log_stage(4, f"Identifying historical versions using strategy: {validation['version_strategy']}")
            version_candidates = self.repo_manager.identify_versions()
            if len(version_candidates) < 2:
                raise ValueError(f"Only {len(version_candidates)} versions identified. Minimum 2 required for evolutionary analysis.")
            self.project_record.total_versions = len(version_candidates)
            self.db.commit()
            self.log_stage(4, f"Selected {len(version_candidates)} versions: {[v['version_tag'] for v in version_candidates]}")

            # Stage 5 & 6 & 7: Version Checkout & Unified Metric Extraction across historical snapshots
            temp_checkout_base = tempfile.mkdtemp(prefix="dna_analysis_")
            created_versions: List[Version] = []
            historical_class_map: Dict[str, List[Dict[str, Any]]] = {} # class_name -> list of version class metrics

            for idx, v_info in enumerate(version_candidates, start=1):
                # Stage 5: Version checkout
                v_tag = v_info["version_tag"]
                c_hash = v_info["commit_hash"]
                self.log_stage(5, f"Checking out version {idx}/{len(version_candidates)}: {v_tag} ({c_hash[:8]})...")
                v_dest = os.path.join(temp_checkout_base, f"v_{idx}")
                self.repo_manager.checkout_version(c_hash, v_dest)

                # Stage 6: Unified metric extraction
                self.log_stage(6, f"Extracting unified metrics for {v_tag} via LanguageAnalyzer registry...")
                metrics_res = default_registry.analyze_repository(v_dest)
                classes_data = metrics_res["classes"]
                proj_data = metrics_res["project"]

                # Strict Data Integrity Verification: every single analyzed file must exist in checked-out snapshot
                for c_dict in classes_data:
                    rel_fpath = c_dict["file_path"]
                    full_check_path = os.path.join(v_dest, rel_fpath)
                    if not os.path.exists(full_check_path):
                        raise ValueError(f"DATA INTEGRITY ERROR: Analyzed source file '{rel_fpath}' does not exist in checked-out commit {c_hash}!")

                # Extract Git evolution metrics relative to previous version
                prev_c_hash = version_candidates[idx - 2]["commit_hash"] if idx > 1 else None
                evo_data = self.repo_manager.extract_evolution_metrics_between(prev_c_hash, c_hash)

                # Persist Version
                ver_obj = Version(
                    project_id=self.project_record.id,
                    version_tag=v_tag,
                    commit_hash=c_hash,
                    commit_date=v_info["commit_date"],
                    order_index=idx,
                    is_release_tag=v_info.get("is_release_tag", False),
                    commit_message=v_info.get("commit_message", ""),
                    author_name=v_info.get("author_name", "")
                )
                self.db.add(ver_obj)
                self.db.flush()

                # Persist Evolution Metric
                evo_obj = EvolutionMetric(
                    version_id=ver_obj.id,
                    commit_count=evo_data.get("commit_count", 1),
                    commit_frequency=evo_data.get("commit_frequency", 1.0),
                    added_lines=evo_data.get("added_lines", 0),
                    deleted_lines=evo_data.get("deleted_lines", 0),
                    code_churn=evo_data.get("code_churn", 0),
                    modified_files_count=evo_data.get("modified_files_count", 0),
                    modified_classes_count=evo_data.get("modified_classes_count", 0),
                    modified_packages_count=evo_data.get("modified_packages_count", 0),
                    avg_time_between_commits_hours=evo_data.get("avg_time_between_commits_hours", 0.0),
                    time_since_prev_version_days=evo_data.get("time_since_prev_version_days", 0.0)
                )
                self.db.add(evo_obj)

                # Persist Project Metric
                proj_obj = ProjectMetric(
                    version_id=ver_obj.id,
                    total_loc=proj_data["total_loc"],
                    avg_loc=proj_data["avg_loc"],
                    avg_wmc=proj_data["avg_wmc"],
                    avg_cbo=proj_data["avg_cbo"],
                    avg_rfc=proj_data["avg_rfc"],
                    avg_lcom=proj_data["avg_lcom"],
                    avg_dit=proj_data["avg_dit"],
                    avg_noc=proj_data["avg_noc"],
                    avg_complexity=proj_data["avg_complexity"],
                    total_methods=proj_data["total_methods"],
                    total_fields=proj_data["total_fields"],
                    total_classes=proj_data["total_classes"],
                    total_packages=proj_data["total_packages"]
                )
                self.db.add(proj_obj)

                # Persist Class Metrics
                for c_dict in classes_data:
                    c_obj = ClassMetric(
                        version_id=ver_obj.id,
                        class_name=c_dict["class_name"],
                        package_name=c_dict["package_name"],
                        file_path=c_dict["file_path"],
                        loc=c_dict["loc"],
                        wmc=c_dict["wmc"],
                        cbo=c_dict["cbo"],
                        rfc=c_dict["rfc"],
                        lcom=c_dict["lcom"],
                        dit=c_dict["dit"],
                        noc=c_dict["noc"],
                        cyclomatic_complexity=c_dict["cyclomatic_complexity"],
                        num_methods=c_dict["num_methods"],
                        num_fields=c_dict["num_fields"],
                        num_public_methods=c_dict["num_public_methods"],
                        num_static_methods=c_dict["num_static_methods"]
                    )
                    self.db.add(c_obj)

                    # Build history map
                    if c_dict["class_name"] not in historical_class_map:
                        historical_class_map[c_dict["class_name"]] = []
                    historical_class_map[c_dict["class_name"]].append(c_dict)

                created_versions.append(ver_obj)
                self.db.flush()

            # Clean temp checkout
            shutil.rmtree(temp_checkout_base, ignore_errors=True)

            # Stage 7: Historical dataset construction
            self.log_stage(7, f"Constructed multi-version historical dataset across {len(created_versions)} versions and {len(historical_class_map)} unique classes.")

            # Stage 8: Evolutionary DNA generation
            self.log_stage(8, "Generating Evolutionary Software DNA profiles across all versions...")
            dna_profiles = []
            for ver in created_versions:
                p_metric = {
                    "avg_complexity": ver.project_metric.avg_complexity,
                    "avg_wmc": ver.project_metric.avg_wmc,
                    "avg_cbo": ver.project_metric.avg_cbo,
                    "avg_rfc": ver.project_metric.avg_rfc,
                    "avg_lcom": ver.project_metric.avg_lcom,
                    "total_loc": ver.project_metric.total_loc,
                    "avg_loc": ver.project_metric.avg_loc,
                }
                e_metric = {
                    "code_churn": ver.evolution_metric.code_churn,
                    "commit_frequency": ver.evolution_metric.commit_frequency,
                    "modified_files_count": ver.evolution_metric.modified_files_count,
                    "added_lines": ver.evolution_metric.added_lines,
                    "deleted_lines": ver.evolution_metric.deleted_lines
                }
                dna_data = EvolutionaryDNAEngine.generate_dna_snapshot(p_metric, e_metric)
                
                dna_obj = DNAProfile(
                    version_id=ver.id,
                    loc=dna_data["loc"],
                    cc=dna_data["cc"],
                    wmc=dna_data["wmc"],
                    cbo=dna_data["cbo"],
                    lcom=dna_data["lcom"],
                    dna_vector=dna_data["dna_vector"],
                    gene_breakdown=dna_data["gene_breakdown"]
                )
                self.db.add(dna_obj)
                dna_profiles.append(dna_data)
            self.db.flush()

            # Stage 9: Mutation analysis
            self.log_stage(9, "Running DNA Mutation Analyzer across consecutive versions...")
            all_mutations: List[Mutation] = []
            for i in range(1, len(created_versions)):
                prev_ver = created_versions[i - 1]
                curr_ver = created_versions[i]

                prev_classes_records = self.db.query(ClassMetric).filter(ClassMetric.version_id == prev_ver.id).all()
                curr_classes_records = self.db.query(ClassMetric).filter(ClassMetric.version_id == curr_ver.id).all()

                prev_classes = [{
                    "class_name": c.class_name, "package_name": c.package_name, "loc": c.loc,
                    "wmc": c.wmc, "cbo": c.cbo, "rfc": c.rfc, "lcom": c.lcom,
                    "cyclomatic_complexity": c.cyclomatic_complexity
                } for c in prev_classes_records]

                curr_classes = [{
                    "class_name": c.class_name, "package_name": c.package_name, "loc": c.loc,
                    "wmc": c.wmc, "cbo": c.cbo, "rfc": c.rfc, "lcom": c.lcom,
                    "cyclomatic_complexity": c.cyclomatic_complexity
                } for c in curr_classes_records]

                muts = MutationAnalyzer.analyze_class_mutations(prev_classes, curr_classes)
                proj_muts = MutationAnalyzer.analyze_project_dna_mutations(
                    dna_profiles[i - 1], dna_profiles[i]
                )

                for m in (muts + proj_muts):
                    m_obj = Mutation(
                        version_id=curr_ver.id,
                        prev_version_id=prev_ver.id,
                        target_type=m["target_type"],
                        module_name=m["module_name"],
                        metric_name=m["metric_name"],
                        previous_value=m["previous_value"],
                        current_value=m["current_value"],
                        delta_value=m["delta_value"],
                        percentage_change=m["percentage_change"],
                        is_deterioration=m["is_deterioration"],
                        severity=m["severity"],
                        reason=m["reason"],
                        is_combined=m["is_combined"],
                        combined_factors=m["combined_factors"]
                    )
                    self.db.add(m_obj)
                    all_mutations.append(m_obj)

            self.db.flush()
            self.log_stage(9, f"Identified {len(all_mutations)} DNA mutations ({len([m for m in all_mutations if m.severity == 'CRITICAL'])} Critical).")

            # Stage 10: ESDI calculation
            self.log_stage(10, "Computing Evolutionary Software DNA Index (ESDI) for each version...")
            version_history_for_prediction = []

            for idx, ver in enumerate(created_versions):
                p_metric = {
                    "avg_complexity": ver.project_metric.avg_complexity,
                    "avg_wmc": ver.project_metric.avg_wmc,
                    "avg_cbo": ver.project_metric.avg_cbo,
                    "avg_rfc": ver.project_metric.avg_rfc,
                    "total_loc": ver.project_metric.total_loc,
                    "total_classes": ver.project_metric.total_classes
                }
                e_metric = {
                    "code_churn": ver.evolution_metric.code_churn,
                    "commit_frequency": ver.evolution_metric.commit_frequency,
                    "modified_files_count": ver.evolution_metric.modified_files_count
                }
                # Dynamic 5D mutation vectors from actual computed mutation records
                ver_muts = []
                for m_dict in (muts + proj_muts if idx > 0 else []):
                    ver_muts.append({
                        "magnitude": m_dict.get("magnitude", 0.0),
                        "persistence": m_dict.get("persistence", 0.0),
                        "acceleration": m_dict.get("acceleration", 0.0),
                        "co_occurrence": m_dict.get("co_occurrence", 0.0),
                        "recency": m_dict.get("recency", 100.0),
                    })
                esdi_dict = ESDIEngine.calculate_esdi(
                    dna_profiles[idx], p_metric, ver_muts if ver_muts else None, self.custom_weights
                )

                esdi_obj = ESDIResult(
                    project_id=self.project_record.id,
                    version_id=ver.id,
                    esdi_score=esdi_dict["esdi_score"],
                    health_score=esdi_dict["health_score"],
                    status=esdi_dict["status"],
                    metric_risk=esdi_dict.get("metric_risk", 0.0),
                    loc_risk=esdi_dict.get("loc_risk", 0.0),
                    cc_risk=esdi_dict.get("cc_risk", 0.0),
                    wmc_risk=esdi_dict.get("wmc_risk", 0.0),
                    cbo_risk=esdi_dict.get("cbo_risk", 0.0),
                    lcom_risk=esdi_dict.get("lcom_risk", 0.0),
                    weighted_loc=esdi_dict.get("weighted_loc", 0.0),
                    weighted_cc=esdi_dict.get("weighted_cc", 0.0),
                    weighted_wmc=esdi_dict.get("weighted_wmc", 0.0),
                    weighted_cbo=esdi_dict.get("weighted_cbo", 0.0),
                    weighted_lcom=esdi_dict.get("weighted_lcom", 0.0),
                    mutation_risk=esdi_dict.get("mutation_risk", 0.0),
                    magnitude_risk=esdi_dict.get("magnitude_risk", 0.0),
                    persistence_risk=esdi_dict.get("persistence_risk", 0.0),
                    acceleration_risk=esdi_dict.get("acceleration_risk", 0.0),
                    co_occurrence_risk=esdi_dict.get("co_occurrence_risk", 0.0),
                    recency_risk=esdi_dict.get("recency_risk", 0.0),
                    complexity_risk=esdi_dict["complexity_risk"],
                    coupling_risk=esdi_dict["coupling_risk"],
                    maintainability_risk=esdi_dict["maintainability_risk"],
                    churn_risk=esdi_dict["churn_risk"],
                    activity_risk=esdi_dict["activity_risk"],
                    defect_risk=esdi_dict["defect_risk"],
                    weighted_complexity=esdi_dict["weighted_complexity"],
                    weighted_coupling=esdi_dict["weighted_coupling"],
                    weighted_maintainability=esdi_dict["weighted_maintainability"],
                    weighted_churn=esdi_dict["weighted_churn"],
                    weighted_activity=esdi_dict["weighted_activity"],
                    weighted_defect=esdi_dict["weighted_defect"],
                    weights_used=esdi_dict["weights_used"],
                    calculation_policy=esdi_dict["calculation_policy"],
                    explanation=esdi_dict["explanation"]
                )
                self.db.add(esdi_obj)

                version_history_for_prediction.append({
                    "version_tag": ver.version_tag,
                    "health_score": esdi_dict["health_score"],
                    "esdi_score": esdi_dict["esdi_score"],
                    "loc": dna_profiles[idx]["loc"],
                    "cc": dna_profiles[idx]["cc"],
                    "wmc": dna_profiles[idx]["wmc"],
                    "cbo": dna_profiles[idx]["cbo"],
                    "lcom": dna_profiles[idx]["lcom"],
                })

            self.db.flush()
            latest_version = created_versions[-1]
            latest_esdi = self.db.query(ESDIResult).filter(ESDIResult.version_id == latest_version.id).first()
            self.log_stage(10, f"Latest ESDI: {latest_esdi.esdi_score}/100 (Health Score: {latest_esdi.health_score}/100).")

            # Stage 11: Module risk analysis & Dual-Condition Gate Enforcement
            self.log_stage(11, f"Analyzing class-level risk for latest version ({latest_version.version_tag})...")
            latest_classes_records = self.db.query(ClassMetric).filter(ClassMetric.version_id == latest_version.id).all()
            latest_mutations_records = self.db.query(Mutation).filter(Mutation.version_id == latest_version.id).all()

            latest_classes = [{
                "class_name": c.class_name, "package_name": c.package_name, "loc": c.loc,
                "wmc": c.wmc, "cbo": c.cbo, "rfc": c.rfc, "lcom": c.lcom,
                "cyclomatic_complexity": c.cyclomatic_complexity
            } for c in latest_classes_records]

            latest_mutations = [{
                "module_name": m.module_name,
                "metric_name": m.metric_name,
                "severity": m.severity,
                "percentage_change": m.percentage_change,
                "is_deterioration": m.is_deterioration,
                "reason": m.reason
            } for m in latest_mutations_records]

            risk_results = ModuleRiskEngine.analyze_all_modules(
                latest_classes, historical_class_map, latest_mutations, latest_esdi.esdi_score
            )

            for r in risk_results:
                r_obj = RiskScore(
                    version_id=latest_version.id,
                    class_name=r["class_name"],
                    package_name=r["package_name"],
                    risk_score=r["risk_score"],
                    priority=r["priority"],
                    top_risk_metric=r["top_risk_metric"],
                    primary_factors=r["primary_factors"],
                    recent_mutation_severity=r["recent_mutation_severity"],
                    esdi_contribution=r["esdi_contribution"],
                    explanation=r["explanation"]
                )
                self.db.add(r_obj)

            # Enforce Section 7.1.E, Equation 15 of IDF-B:
            max_unit_risk = max([r["risk_score"] for r in risk_results]) if risk_results else 0.0
            critical_units = [r["class_name"] for r in risk_results if r["risk_score"] >= 90.0]
            blocked_units = [r["class_name"] for r in risk_results if 80.0 <= r["risk_score"] < 90.0]
            warn_units = [r["class_name"] for r in risk_results if 50.0 <= r["risk_score"] < 80.0]

            if latest_esdi.esdi_score >= 80.0 or max_unit_risk >= 90.0:
                final_gate_status = "CRITICAL BLOCK"
                culprit = f"Unit '{critical_units[0]}' Unit Risk = {max([r['risk_score'] for r in risk_results if r['class_name'] == critical_units[0]]):.1f}/100 >= 90.0" if critical_units else f"ESDI = {latest_esdi.esdi_score:.1f}/100 >= 80.0"
                gate_explanation = f"CRITICAL RISK: {culprit}. Branch quarantined."
            elif (65.0 <= latest_esdi.esdi_score < 80.0) or (80.0 <= max_unit_risk < 90.0):
                final_gate_status = "BLOCK"
                culprit = f"Unit '{blocked_units[0]}' Unit Risk = {max_unit_risk:.1f}/100 >= 80.0" if blocked_units else f"ESDI = {latest_esdi.esdi_score:.1f}/100 >= 65.0"
                gate_explanation = f"HIGH RISK: {culprit}. Build blocked."
            elif (35.0 <= latest_esdi.esdi_score < 65.0) or (50.0 <= max_unit_risk < 80.0):
                final_gate_status = "WARN"
                gate_explanation = f"MODERATE RISK: Review recommended (ESDI={latest_esdi.esdi_score:.1f}/100, Max Unit Risk={max_unit_risk:.1f}/100)."
            else:
                final_gate_status = "PASS"
                gate_explanation = f"Evolutionary software DNA stable within healthy boundaries (ESDI={latest_esdi.esdi_score:.1f}/100, Max Unit Risk={max_unit_risk:.1f}/100)."

            latest_esdi.status = final_gate_status
            latest_esdi.explanation = gate_explanation
            self.db.flush()

            self.log_stage(11, f"Evaluated {len(risk_results)} modules. Peak Unit Risk: {max_unit_risk:.1f}/100. CI/CD Gate Decision: {final_gate_status}.")

            # Stage 12: Recommendation generation
            self.log_stage(12, "Generating explainable, evidence-backed AI recommendations...")
            recs = RecommendationEngine.generate_recommendations(
                latest_classes, historical_class_map, latest_mutations, risk_results, {"esdi": latest_esdi.esdi_score}
            )

            for rec in recs:
                rec_obj = Recommendation(
                    project_id=self.project_record.id,
                    version_id=latest_version.id,
                    priority=rec["priority"],
                    module_name=rec["module_name"],
                    metric_name=rec["metric_name"],
                    current_value=rec["current_value"],
                    observed_trend=rec["observed_trend"],
                    percentage_change=rec["percentage_change"],
                    mutation_severity=rec["mutation_severity"],
                    target=rec["target"],
                    reason=rec["reason"],
                    recommended_action=rec["recommended_action"],
                    expected_benefit=rec["expected_benefit"],
                    evidence=rec["evidence"],
                    is_ml_derived=rec.get("is_ml_derived", False)
                )
                self.db.add(rec_obj)

            self.db.flush()
            self.log_stage(12, f"Synthesized {len(recs)} prioritized actionable recommendations.")

            # Stage 13: Future prediction
            self.log_stage(13, "Computing next-version future quality and risk trajectory...")
            pred_data = QualityPredictionEngine.predict_future_quality(
                version_history_for_prediction,
                gate_decision=latest_esdi.status,
                max_unit_risk=max_unit_risk
            )

            pred_obj = Prediction(
                project_id=self.project_record.id,
                current_version_id=latest_version.id,
                current_health=pred_data["current_health"],
                predicted_health=pred_data["predicted_health"],
                predicted_esdi=pred_data["predicted_esdi"],
                trend_direction=pred_data["trend_direction"],
                confidence_score=pred_data["confidence_score"],
                is_data_sufficient=pred_data["is_data_sufficient"],
                status_message=pred_data["status_message"],
                main_factors=pred_data["main_factors"],
                forecast_points=pred_data["forecast_points"]
            )
            self.db.add(pred_obj)
            self.db.flush()
            self.log_stage(13, f"Future Prediction: {pred_data['status_message']}")

            # Stage 14: Report generation & persistence
            self.log_stage(14, "Finalizing report and persisting all historical data...")
            self.project_record.total_classes = latest_version.project_metric.total_classes
            self.project_record.total_packages = latest_version.project_metric.total_packages

            self.run_record.status = "COMPLETED"
            self.run_record.current_stage = "Completed"
            self.run_record.stage_index = 14
            self.run_record.completed_at = datetime.datetime.utcnow()
            self.db.commit()

            self.log_stage(14, f"Analysis successfully completed for project '{self.project_record.name}' (ID: {self.project_record.id}).")

            return {
                "success": True,
                "project_id": self.project_record.id,
                "project_name": self.project_record.name,
                "total_versions": len(created_versions),
                "health_score": latest_esdi.health_score,
                "esdi_score": latest_esdi.esdi_score,
                "status": latest_esdi.status
            }

        except Exception as e:
            self.db.rollback()
            err_msg = str(e)
            print(f"Analysis failed: {err_msg}")
            if self.run_record:
                self.run_record.status = "FAILED"
                self.run_record.error_message = err_msg
                if self.run_record.logs is None:
                    self.run_record.logs = []
                logs_copy = list(self.run_record.logs)
                logs_copy.append(f"ERROR: {err_msg}")
                self.run_record.logs = logs_copy
                self.db.commit()
            return {
                "success": False,
                "error": err_msg,
                "project_id": self.project_record.id if self.project_record else None
            }
