# This tests that we can use our custom vtkMRMLLayerDMPipelineI subclass
# with the vtkMRMLLayerDMPipelineScriptedCreator and vtkMRMLLayerDMPipelineFactory

from slicer import (
    vtkMRMLLayerDMPipelineFactory,
    vtkMRMLLayerDMPipelineScriptedCreator,
    vtkMRMLModelGlowPipeline,
)

factory = vtkMRMLLayerDMPipelineFactory()
creator = vtkMRMLLayerDMPipelineScriptedCreator()
creator.SetPythonCallback(lambda *_: vtkMRMLModelGlowPipeline())
factory.AddPipelineCreator(creator)
assert isinstance(factory.CreatePipeline(None, None), vtkMRMLModelGlowPipeline)
