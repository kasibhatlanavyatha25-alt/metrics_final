import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    language = Column(String(50), default='Java')
    first_commit_date = Column(DateTime, nullable=True)
    latest_commit_date = Column(DateTime, nullable=True)
    total_commits = Column(Integer, default=0)
    total_java_files = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    total_packages = Column(Integer, default=0)
    total_versions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    versions = relationship('Version', back_populates='project', cascade='all, delete-orphan', order_by='Version.order_index')
    analysis_runs = relationship('AnalysisRun', back_populates='project', cascade='all, delete-orphan')
    esdi_results = relationship('ESDIResult', back_populates='project', cascade='all, delete-orphan')
    recommendations = relationship('Recommendation', back_populates='project', cascade='all, delete-orphan')
    predictions = relationship('Prediction', back_populates='project', cascade='all, delete-orphan')

class Version(Base):
    __tablename__ = 'versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    version_tag = Column(String(100), nullable=False) # e.g. "V1", "v1.0.0", or commit tag
    commit_hash = Column(String(64), nullable=False)
    commit_date = Column(DateTime, nullable=False)
    order_index = Column(Integer, nullable=False) # 1, 2, 3, 4, ...
    is_release_tag = Column(Boolean, default=False)
    commit_message = Column(Text, nullable=True)
    author_name = Column(String(255), nullable=True)

    project = relationship('Project', back_populates='versions')
    commits = relationship('Commit', back_populates='version', cascade='all, delete-orphan')
    class_metrics = relationship('ClassMetric', back_populates='version', cascade='all, delete-orphan')
    project_metric = relationship('ProjectMetric', back_populates='version', uselist=False, cascade='all, delete-orphan')
    evolution_metric = relationship('EvolutionMetric', back_populates='version', uselist=False, cascade='all, delete-orphan')
    dna_profile = relationship('DNAProfile', back_populates='version', uselist=False, cascade='all, delete-orphan')
    mutations = relationship('Mutation', foreign_keys='Mutation.version_id', back_populates='version', cascade='all, delete-orphan')
    risk_scores = relationship('RiskScore', back_populates='version', cascade='all, delete-orphan')

class Commit(Base):
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    author = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=False)
    message = Column(Text, nullable=True)
    added_lines = Column(Integer, default=0)
    deleted_lines = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)

    version = relationship('Version', back_populates='commits')

class ClassMetric(Base):
    __tablename__ = 'class_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    class_name = Column(String(255), nullable=False)
    package_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    
    # CK & OO Metrics
    loc = Column(Integer, default=0) # Lines of Code
    wmc = Column(Integer, default=0) # Weighted Methods per Class
    cbo = Column(Integer, default=0) # Coupling Between Objects
    rfc = Column(Integer, default=0) # Response For a Class
    lcom = Column(Float, default=0.0) # Lack of Cohesion of Methods
    dit = Column(Integer, default=0) # Depth of Inheritance Tree
    noc = Column(Integer, default=0) # Number of Children
    cyclomatic_complexity = Column(Integer, default=0)
    num_methods = Column(Integer, default=0)
    num_fields = Column(Integer, default=0)
    num_public_methods = Column(Integer, default=0)
    num_static_methods = Column(Integer, default=0)

    version = relationship('Version', back_populates='class_metrics')

class ProjectMetric(Base):
    __tablename__ = 'project_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    total_loc = Column(Integer, default=0)
    avg_loc = Column(Float, default=0.0)
    avg_wmc = Column(Float, default=0.0)
    avg_cbo = Column(Float, default=0.0)
    avg_rfc = Column(Float, default=0.0)
    avg_lcom = Column(Float, default=0.0)
    avg_dit = Column(Float, default=0.0)
    avg_noc = Column(Float, default=0.0)
    avg_complexity = Column(Float, default=0.0)
    total_methods = Column(Integer, default=0)
    total_fields = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    total_packages = Column(Integer, default=0)

    version = relationship('Version', back_populates='project_metric')

class EvolutionMetric(Base):
    __tablename__ = 'evolution_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    commit_count = Column(Integer, default=0)
    commit_frequency = Column(Float, default=0.0) # commits per day/week
    added_lines = Column(Integer, default=0)
    deleted_lines = Column(Integer, default=0)
    code_churn = Column(Integer, default=0) # Added + Deleted
    modified_files_count = Column(Integer, default=0)
    modified_classes_count = Column(Integer, default=0)
    modified_packages_count = Column(Integer, default=0)
    avg_time_between_commits_hours = Column(Float, default=0.0)
    time_since_prev_version_days = Column(Float, default=0.0)

    version = relationship('Version', back_populates='evolution_metric')

class DNAProfile(Base):
    __tablename__ = 'dna_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    # Canonical 5 Software DNA Metrics
    loc = Column(Float, default=0.0) # Lines of Code
    cc = Column(Float, default=0.0)  # Cyclomatic Complexity
    wmc = Column(Float, default=0.0) # Weighted Methods per Class
    cbo = Column(Float, default=0.0) # Coupling Between Objects
    lcom = Column(Float, default=0.0) # Lack of Cohesion of Methods
    
    # Canonical DNA vector: [LOC, CC, WMC, CBO, LCOM]
    dna_vector = Column(JSON, nullable=True)
    gene_breakdown = Column(JSON, nullable=True)

    # Legacy/compatibility aliases
    @property
    def complexity_gene(self):
        return self.cc
    
    @property
    def coupling_gene(self):
        return self.cbo
    
    @property
    def cohesion_gene(self):
        return round(max(0.0, min(1.0, 1.0 - self.lcom)) * 100.0, 2)
    
    @property
    def size_gene(self):
        return self.loc
    
    @property
    def maintainability_gene(self):
        return round(max(0.0, min(100.0, 100.0 - (self.cc * 2.0 + self.cbo * 3.0))), 2)
    
    @property
    def churn_gene(self):
        return 0.0

    @property
    def activity_gene(self):
        return 0.0

    @property
    def defect_gene(self):
        return None

    version = relationship('Version', back_populates='dna_profile')

class Mutation(Base):
    __tablename__ = 'mutations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    prev_version_id = Column(Integer, ForeignKey('versions.id'), nullable=True)
    target_type = Column(String(50), default='CLASS') # CLASS, MODULE or PROJECT
    module_name = Column(String(255), nullable=False)
    metric_name = Column(String(100), nullable=False)
    previous_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    delta_value = Column(Float, nullable=False)
    percentage_change = Column(Float, nullable=False)
    is_deterioration = Column(Boolean, default=False)
    severity = Column(String(50), nullable=False) # HEALTHY, RISKY, CRITICAL
    
    # 5 Mutation Dimensions
    magnitude = Column(Float, default=0.0)
    persistence = Column(Float, default=0.0) # 0 to 100%
    acceleration = Column(Float, default=0.0) # second difference normalized
    co_occurrence = Column(Float, default=0.0) # 0 to 100%
    recency = Column(Float, default=0.0) # 0 to 100%
    composite_mutation_score = Column(Float, default=0.0)
    
    reason = Column(Text, nullable=False)
    is_combined = Column(Boolean, default=False)
    combined_factors = Column(JSON, nullable=True)

    version = relationship('Version', foreign_keys=[version_id], back_populates='mutations')

class ESDIResult(Base):
    __tablename__ = 'esdi_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    esdi_score = Column(Float, nullable=False) # 0 to 100
    health_score = Column(Float, nullable=False) # 100 - ESDI
    status = Column(String(50), nullable=False) # PASS, WARN, BLOCK, CRITICAL BLOCK
    
    # DNA Metric Risk Components (0 - 100)
    metric_risk = Column(Float, default=0.0)
    loc_risk = Column(Float, default=0.0)
    cc_risk = Column(Float, default=0.0)
    wmc_risk = Column(Float, default=0.0)
    cbo_risk = Column(Float, default=0.0)
    lcom_risk = Column(Float, default=0.0)
    
    weighted_loc = Column(Float, default=0.0)
    weighted_cc = Column(Float, default=0.0)
    weighted_wmc = Column(Float, default=0.0)
    weighted_cbo = Column(Float, default=0.0)
    weighted_lcom = Column(Float, default=0.0)
    
    # 5D Mutation Dimension Risk Components (0 - 100)
    mutation_risk = Column(Float, default=0.0)
    magnitude_risk = Column(Float, default=0.0)
    persistence_risk = Column(Float, default=0.0)
    acceleration_risk = Column(Float, default=0.0)
    co_occurrence_risk = Column(Float, default=0.0)
    recency_risk = Column(Float, default=0.0)

    # Legacy compatibility fields
    complexity_risk = Column(Float, default=0.0)
    coupling_risk = Column(Float, default=0.0)
    maintainability_risk = Column(Float, default=0.0)
    churn_risk = Column(Float, default=0.0)
    activity_risk = Column(Float, default=0.0)
    defect_risk = Column(Float, nullable=True)

    weighted_complexity = Column(Float, default=0.0)
    weighted_coupling = Column(Float, default=0.0)
    weighted_maintainability = Column(Float, default=0.0)
    weighted_churn = Column(Float, default=0.0)
    weighted_activity = Column(Float, default=0.0)
    weighted_defect = Column(Float, nullable=True)

    metric_weights = Column(JSON, nullable=True)
    mutation_weights = Column(JSON, nullable=True)
    weights_used = Column(JSON, nullable=False)
    calculation_policy = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)

    project = relationship('Project', back_populates='esdi_results')
    version = relationship('Version')

class RiskScore(Base):
    __tablename__ = 'risk_scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    class_name = Column(String(255), nullable=False)
    package_name = Column(String(255), nullable=True)
    risk_score = Column(Float, nullable=False) # 0 - 100
    priority = Column(String(50), nullable=False) # CRITICAL, HIGH, MEDIUM, LOW
    top_risk_metric = Column(String(100), nullable=False)
    primary_factors = Column(JSON, nullable=False) # list of dicts with metrics and reasons
    recent_mutation_severity = Column(String(50), nullable=True)
    esdi_contribution = Column(Float, default=0.0)
    explanation = Column(Text, nullable=False)

    version = relationship('Version', back_populates='risk_scores')

class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    priority = Column(String(50), nullable=False) # CRITICAL, HIGH, MEDIUM, LOW
    module_name = Column(String(255), nullable=False)
    metric_name = Column(String(100), nullable=False)
    current_value = Column(Float, nullable=False)
    observed_trend = Column(String(255), nullable=False) # "8 -> 10 -> 15 -> 22"
    percentage_change = Column(Float, nullable=False)
    mutation_severity = Column(String(50), nullable=False)
    target = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    expected_benefit = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    is_ml_derived = Column(Boolean, default=False)

    project = relationship('Project', back_populates='recommendations')
    version = relationship('Version')

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    current_version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    current_health = Column(Float, nullable=False)
    predicted_health = Column(Float, nullable=True)
    predicted_esdi = Column(Float, nullable=True)
    trend_direction = Column(String(50), nullable=False) # IMPROVING, STABLE, DECLINING, INSUFFICIENT_DATA
    confidence_score = Column(Float, nullable=True)
    is_data_sufficient = Column(Boolean, default=True)
    status_message = Column(Text, nullable=False)
    main_factors = Column(JSON, nullable=True)
    forecast_points = Column(JSON, nullable=True) # historical + forecast points for charting

    project = relationship('Project', back_populates='predictions')
    current_version = relationship('Version')

class AnalysisRun(Base):
    __tablename__ = 'analysis_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    status = Column(String(50), default='PENDING') # PENDING, RUNNING, COMPLETED, FAILED
    current_stage = Column(String(100), nullable=True)
    stage_index = Column(Integer, default=0) # 1 to 14
    total_stages = Column(Integer, default=14)
    logs = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship('Project', back_populates='analysis_runs')
