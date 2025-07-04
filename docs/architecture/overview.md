# System Architecture Overview

> **Status**: Production-ready implementation with enterprise-grade quality standards

## 🏗️ High-Level Architecture

The Warp Content Processor is built as a modular, security-first system designed to handle robust parsing and processing of mixed, mangled, and contaminated content. The architecture follows SOLID principles and implements comprehensive error handling with graceful degradation.

## 📋 System Components

### Core Processing Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Input    │───▶│  Content Split  │───▶│ Type Detection  │
│   Validation    │    │  & Archaeology  │    │ & Classification │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Security     │    │    Schema       │    │    Content      │
│   Validation    │    │   Extraction    │    │  Normalization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Robust YAML    │    │   Processor     │    │   Organized     │
│    Parsing      │    │    Factory      │    │    Output       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🎯 Key Architectural Patterns

1. **Factory Pattern**: `ProcessorFactory` creates appropriate processors for each content type
2. **Strategy Pattern**: Multiple parsing strategies with progressive fallback
3. **Chain of Responsibility**: Content processing pipeline with error handling
4. **Observer Pattern**: Comprehensive logging and monitoring throughout
5. **Template Method**: Base processor defines common processing flow

## 🔧 Component Details

### 1. Content Processor (`ContentProcessor`)
**Location**: `src/warp_content_processor/schema_processor.py`
**Purpose**: Main orchestrator for all content processing operations

**Key Responsibilities**:
- File input validation and security checking
- Content splitting and document separation
- Processor delegation and result aggregation
- Output file generation with unique naming

### 2. Content Archaeologist (`ContentArchaeologist`)
**Location**: `src/warp_content_processor/excavation/archaeologist.py`
**Purpose**: Intelligent extraction of schema from contaminated content

**Key Capabilities**:
- Schema island detection in mixed content
- Content contamination analysis
- Confidence scoring for extracted artifacts
- Performance monitoring and timeout protection

### 3. Schema Island Detector (`SchemaIslandDetector`)
**Location**: `src/warp_content_processor/excavation/island_detector.py`
**Purpose**: Pattern recognition for embedded content structures

**Detection Strategies**:
- YAML structure pattern matching
- JSON object detection and validation
- Content quality scoring algorithms
- Overlap detection and removal

### 4. Robust YAML Parser (`ErrorTolerantYAMLParser`)
**Location**: `src/warp_content_processor/parsers/error_tolerant_yaml.py`
**Purpose**: Multi-strategy YAML parsing with progressive degradation

**Parsing Strategies**:
1. **Standard**: Fast path for well-formed YAML
2. **Cleaned**: Content cleaning before parsing
3. **Mangled**: Advanced reconstruction for damaged content
4. **Partial**: Extract valid portions from broken content
5. **Reconstructed**: Intelligent structure rebuilding

### 5. Security Validation (`ContentSanitizer`)
**Location**: `src/warp_content_processor/utils/security_normalization.py`
**Purpose**: Comprehensive input validation and sanitization

**Security Features**:
- XSS and script injection prevention
- Command injection protection
- Path traversal validation
- Content size and structure limits
- Unicode normalization and validation

## 🛡️ Security Architecture

### Defense in Depth Strategy

1. **Input Validation**: All file paths and content validated before processing
2. **Content Sanitization**: Pattern-based scanning for malicious content
3. **Resource Limits**: Configurable timeouts and size restrictions
4. **Error Isolation**: Secure error handling with information leakage prevention
5. **Output Sanitization**: All generated content validated before writing

### Security Boundaries

```
External Input ──▶ [Path Validation] ──▶ [Content Validation] ──▶ [Processing]
                         │                       │                     │
                         ▼                       ▼                     ▼
                  SecurityError           SecurityError        Validated Output
```

## 📊 Performance Characteristics

### Current Metrics
- **Test Execution**: 222 tests in 0.18s (sub-second performance)
- **Memory Efficiency**: Configurable content size limits
- **Timeout Protection**: Configurable processing timeouts
- **Error Recovery**: Graceful degradation with fallback strategies

### Scalability Design
- **Streaming Processing**: Large content handled in chunks
- **Resource Management**: Configurable limits for memory and time
- **Early Termination**: Efficient parsing with early success detection
- **Caching Strategy**: Minimal memory footprint with selective caching

## 🔄 Data Flow

### Processing Workflow

1. **Ingestion Phase**
   - File path validation and security checks
   - Content reading with encoding detection
   - Initial content sanitization

2. **Analysis Phase**
   - Content archaeology and island detection
   - Document splitting and separation
   - Content type classification

3. **Processing Phase**
   - Type-specific processor selection
   - Robust parsing with fallback strategies
   - Content normalization and validation

4. **Output Phase**
   - Filename generation with uniqueness
   - Organized directory structure creation
   - Secure file writing with validation

## 🧩 Extension Points

The architecture provides several extension points for future enhancements:

### Content Type Processors
- **Interface**: `SchemaProcessor` base class
- **Location**: `src/warp_content_processor/base_processor.py`
- **Extension**: Add new processor classes for additional content types

### Parsing Strategies
- **Interface**: Strategy pattern in `ErrorTolerantYAMLParser`
- **Location**: `src/warp_content_processor/parsers/error_tolerant_yaml.py`
- **Extension**: Add new parsing strategies for complex content

### Security Validators
- **Interface**: Pattern-based validation in `ContentSanitizer`
- **Location**: `src/warp_content_processor/utils/security_normalization.py`
- **Extension**: Add new security patterns and validation rules

## 🎖️ Quality Assurance

### Code Quality Standards
- **Type Safety**: Comprehensive type hints throughout
- **Error Handling**: Explicit exception handling with proper recovery
- **Documentation**: Docstrings for all public methods and classes
- **Testing**: 100% test coverage with parametrized, conditional-free tests

### Performance Standards
- **Efficiency**: Sub-second execution for typical workloads
- **Memory Management**: Bounded memory usage with configurable limits
- **Timeout Protection**: Configurable timeouts prevent infinite loops
- **Resource Cleanup**: Proper resource management and cleanup

---

*This architecture documentation reflects the current production-ready implementation with enterprise-grade quality standards achieved through comprehensive testing, security validation, and performance optimization.*
