# Laboratory vs Radiology Department Separation

## Current Issue Analysis

The current system has mixed up Laboratory and Radiology departments:

### Problems Identified:
1. **Mixed Templates**: `/templates/diagnostics/` contains lab templates but uses "diagnostics" naming
2. **Confused Terminology**: "Diagnostic" is too generic and doesn't distinguish between lab and radiology
3. **Missing Radiology Module**: No separate radiology app exists
4. **API Views in Laboratory**: Laboratory module uses DRF ViewSets instead of proper Django views

## Proposed Solution

### 1. Laboratory Department
**Scope**: Blood tests, urine analysis, biochemistry, hematology, microbiology
- **Models**: LabTest, LabOrder, LabOrderItem, LabResult, TestCategory
- **Tests Examples**: CBC, Blood Sugar, Liver Function, Kidney Function, Cholesterol, etc.

### 2. Radiology Department  
**Scope**: Medical imaging and radiological examinations
- **Models**: ImagingStudy, RadiologyOrder, ImagingResult, StudyType
- **Tests Examples**: X-Ray, CT Scan, MRI, Ultrasound, Mammography, etc.

## Implementation Plan

### Phase 1: Fix Laboratory Module
1. ✅ Replace API views with proper Django views
2. ✅ Create proper forms for laboratory
3. ✅ Move templates from `/diagnostics/` to `/laboratory/`
4. ✅ Update URL patterns
5. ✅ Fix MRO issues in views

### Phase 2: Create Radiology Module
1. Create radiology models
2. Create radiology views and forms
3. Create radiology templates
4. Add radiology URLs
5. Update main navigation

### Phase 3: Clean Up
1. Remove old diagnostics templates
2. Update references in other modules
3. Add proper permissions
4. Test integration

## Department Characteristics

### Laboratory
- **Sample Collection**: Physical samples (blood, urine, etc.)
- **Processing Time**: Hours to days
- **Results**: Numerical values, text reports
- **Equipment**: Analyzers, microscopes, centrifuges

### Radiology
- **Image Acquisition**: Digital images via medical equipment
- **Processing Time**: Minutes to hours
- **Results**: Images with radiologist interpretation
- **Equipment**: X-ray machines, CT scanners, MRI, ultrasound

## Benefits of Separation

1. **Clear Responsibility**: Each department has distinct workflows
2. **Specialized Features**: Lab focuses on sample tracking, Radiology on image management
3. **Better Organization**: Easier for staff to navigate
4. **Scalability**: Each module can evolve independently
5. **Compliance**: Better adherence to medical standards
