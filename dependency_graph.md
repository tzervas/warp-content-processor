# Module Dependency Graph

## Import Relationship Mapping

### Core Package Structure with Dependencies

```
warp_content_processor/
│
├── __init__.py
│   ├── imports: base_processor.{ProcessingResult, SchemaProcessor}
│   ├── imports: processors.{EnvVarProcessor, NotebookProcessor, PromptProcessor, RuleProcessor}
│   ├── imports: schema_processor.{ContentProcessor, ContentSplitter, ContentType, ContentTypeDetector}
│   └── imports: workflow_processor.{WorkflowProcessor, WorkflowValidator}
│
├── base_processor.py
│   ├── imports: abc.{ABC, abstractmethod}
│   ├── imports: dataclasses.dataclass
│   └── imports: typing.{Any, Dict, List, Optional, Set, Tuple}
│
├── content_type.py
│   └── imports: enum.Enum
│
├── main.py
│   ├── imports: logging, sys, pathlib.Path, typing.{Dict, List, Union}
│   ├── imports: .base_processor.ProcessingResult
│   └── imports: .schema_processor.ContentProcessor
│
├── processor_factory.py
│   ├── imports: pathlib.Path, typing.{Any, Dict, Optional, Union}
│   ├── imports: .base_processor.SchemaProcessor
│   ├── imports: .content_type.ContentType
│   └── dynamic imports: {workflow_processor, processors.*}
│
├── schema_processor.py
│   ├── imports: logging, re, pathlib.Path, typing.{Dict, List, Tuple, Union}
│   ├── imports: yaml
│   ├── imports: .base_processor.{ProcessingResult, SchemaProcessor}
│   ├── imports: .content_type.ContentType
│   └── imports: .processor_factory.ProcessorFactory
│
├── workflow_processor.py
│   ├── imports: logging, os, re, pathlib.Path, typing.{Any, Dict, List, Optional, Tuple}
│   ├── imports: yaml
│   ├── imports: .base_processor.{ProcessingResult, SchemaProcessor}
│   ├── imports: .content_type.ContentType
│   └── imports: .utils.validation.{validate_placeholders, validate_tags}
│
├── parse_yaml.py
│   ├── imports: pathlib.Path, typing.{Any, Dict, List, Optional}
│   └── imports: yaml
│
└── processors/
    │
    ├── __init__.py
    │   ├── imports: ..base_processor.{ProcessingResult, SchemaProcessor}
    │   ├── imports: ..content_type.ContentType
    │   └── imports: .{env_var_processor, notebook_processor, prompt_processor, rule_processor}
    │
    ├── env_var_processor.py
    │   ├── imports: logging, re, typing.{Dict, List, Tuple}
    │   ├── imports: yaml
    │   ├── imports: ..base_processor.{ProcessingResult, SchemaProcessor}
    │   └── imports: ..content_type.ContentType
    │
    ├── notebook_processor.py
    │   ├── imports: logging, re, typing.{Dict, List, Optional, Tuple}
    │   ├── imports: yaml
    │   ├── imports: ..base_processor.{ProcessingResult, SchemaProcessor}
    │   └── imports: ..content_type.ContentType
    │
    ├── prompt_processor.py
    │   ├── imports: logging, re, typing.{Dict, List, Tuple}
    │   ├── imports: yaml
    │   ├── imports: ..base_processor.{ProcessingResult, SchemaProcessor}
    │   └── imports: ..content_type.ContentType
    │
    └── rule_processor.py
        ├── imports: logging, re, typing.{Dict, List, Tuple}
        ├── imports: yaml
        ├── imports: ..base_processor.{ProcessingResult, SchemaProcessor}
        └── imports: ..content_type.ContentType

└── parsers/ (NEW in feat/robust-mangled-content-parsing)
    │
    ├── __init__.py
    │   └── imports: .{base, common_patterns, content_detector, document_splitter}
    │
    ├── base.py (NEW)
    │   ├── imports: abc.{ABC, abstractmethod}
    │   ├── imports: dataclasses.dataclass
    │   └── imports: typing.{Any, Dict, List, Optional, Union}
    │
    ├── common_patterns.py (NEW)
    │   ├── imports: re, typing.{Dict, List, Pattern, Set}
    │   └── potential imports: .base.{ParseResult, ParsingStrategy}
    │
    ├── content_detector.py (NEW)
    │   ├── imports: re, typing.{Dict, List, Optional, Set}
    │   └── potential imports: ..content_type.ContentType
    │
    ├── document_splitter.py (MODIFIED)
    │   ├── imports: re, typing.{List, Tuple}
    │   ├── imports: yaml
    │   ├── imports: ..base_processor.ProcessingResult
    │   └── imports: ..content_type.ContentType
    │
    ├── intelligent_cleaner.py (NEW)
    │   └── imports: re, typing.{Dict, List, Optional, Set, Tuple}
    │
    ├── robust_parser.py (NEW)
    │   ├── imports: logging, re, typing.{Any, Dict, List, Optional}
    │   └── imports: yaml
    │
    └── yaml_strategies.py (NEW)
        ├── imports: logging, re, typing.{Any, Dict, List, Optional, Union}
        └── imports: yaml

└── utils/
    │
    ├── __init__.py
    │   └── (empty or minimal imports)
    │
    ├── normalizer.py
    │   ├── imports: re, typing.{Any, Dict, List, Optional, Union}
    │   └── imports: ..content_type.ContentType
    │
    ├── security.py (NEW in feat/robust-mangled-content-parsing)
    │   ├── imports: hashlib, logging, re, typing.{Any, Dict, List, Optional, Set}
    │   └── potential external imports: security frameworks
    │
    ├── validation.py
    │   ├── imports: re, dataclasses.dataclass, typing.{Any, Dict, List, Optional, Pattern, Set, Tuple, Union}
    │   └── no internal imports
    │
    └── yaml_parser.py
        ├── imports: pathlib.Path, typing.{Any, Dict, List, Optional, Union}
        └── imports: yaml

└── excavation/
    │
    ├── __init__.py
    │   ├── imports: pathlib.Path, typing.{Any, Dict, List, Optional, Tuple, Union}
    │   ├── imports: .archaeologist.{Archaeologist, ArtifactSummary}
    │   ├── imports: .artifacts.{ArtifactType, ProcessingArtifact}
    │   └── imports: .island_detector.IslandDetector
    │
    ├── archaeologist.py
    │   ├── imports: logging, pathlib.Path, typing.{Any, Dict, List, Optional, Tuple, Union}
    │   ├── imports: yaml
    │   ├── imports: ..base_processor.ProcessingResult
    │   ├── imports: ..content_type.ContentType
    │   ├── imports: ..processor_factory.ProcessorFactory
    │   ├── imports: ..schema_processor.{ContentSplitter, ContentTypeDetector}
    │   └── imports: .artifacts.{ArtifactType, ProcessingArtifact}
    │
    ├── artifacts.py
    │   ├── imports: dataclasses.dataclass, enum.Enum, pathlib.Path, typing.{Any, Dict, List, Optional}
    │   └── no internal imports
    │
    └── island_detector.py
        ├── imports: logging, re, typing.{Dict, List, Optional, Set, Tuple}
        ├── imports: yaml
        └── imports: ..content_type.ContentType
```

## Dependency Flow Analysis

### External Dependencies
```
PyYAML (yaml) ← Used by almost all modules for YAML processing
├── schema_processor.py
├── workflow_processor.py  
├── all processors/*
├── parse_yaml.py
├── utils/yaml_parser.py
├── excavation/archaeologist.py
├── excavation/island_detector.py
└── parsers/{document_splitter, robust_parser, yaml_strategies}

Standard Library (logging, re, pathlib, typing, abc, dataclasses, enum)
└── Used throughout all modules

Test Dependencies (pytest, pytest-cov, pytest-timeout)
└── Used in test files only
```

### Internal Dependency Levels

#### Level 1: Foundation (No internal dependencies)
- content_type.py
- base_processor.py 
- utils/validation.py
- excavation/artifacts.py

#### Level 2: Core Building Blocks  
- utils/normalizer.py (depends on content_type)
- utils/yaml_parser.py (no internal deps)
- parse_yaml.py (no internal deps)
- parsers/base.py (no internal deps)

#### Level 3: Specialized Components
- All processors/* (depend on base_processor, content_type)
- parsers/* components (depend on base, potentially content_type)
- utils/security.py (minimal internal deps)
- excavation/island_detector.py (depends on content_type)

#### Level 4: Integration Layer
- processor_factory.py (depends on base_processor, content_type, dynamic imports)
- excavation/archaeologist.py (depends on multiple modules)

#### Level 5: High-Level Orchestration  
- schema_processor.py (depends on base_processor, content_type, processor_factory)
- workflow_processor.py (depends on base_processor, content_type, utils/validation)

#### Level 6: Application Layer
- main.py (depends on base_processor, schema_processor)
- __init__.py (depends on all major components)

## Circular Dependency Risks

### Potential Circular Dependencies
1. **parsers package ↔ content_type**: If parsers import content_type and content_type imports parsers
2. **schema_processor ↔ processor_factory**: Factory creates processors, but schema_processor uses factory
3. **excavation/archaeologist ↔ schema_processor**: Archaeologist uses schema components, but schema might use excavation

### Mitigation Strategies
1. Use lazy imports in factory patterns
2. Define interfaces in separate modules
3. Use dependency injection where possible
4. Keep utils modules dependency-free

## Breaking Change Impact Analysis

### High Impact Changes
- **base_processor.py**: Changes affect ALL processors
- **content_type.py**: Changes affect most modules  
- **schema_processor.py**: Core integration point
- **__init__.py**: Changes affect external API

### Medium Impact Changes  
- **processor_factory.py**: Affects processor instantiation
- **workflow_processor.py**: Affects workflow processing
- **processors/***: Affects specific content types

### Low Impact Changes
- **utils/***: Typically isolated changes
- **excavation/***: Specialized functionality
- **parse_yaml.py**: Limited scope
