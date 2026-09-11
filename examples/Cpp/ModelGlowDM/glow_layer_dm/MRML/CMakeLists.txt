set(classes_glow vtkMRMLModelGlowPipeline vtkMRMLModelGlowDisplayNode)
set(headers_glow vtkMRLMModelGlowLayerDMLogic.h)

vtk_module_add_module(Slicer::ModelGlowModuleMRMLExport
  EXPORT_MACRO_PREFIX VTK_SLICER_MODEL_GLOW_MODULE_MRML
  CLASSES ${classes_glow}
  HEADERS ${headers_glow}
)
