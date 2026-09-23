#pragma once

#include "vtkMRMLLayerDMPipelineCreatorI.h"
#include "vtkMRMLLayerDMPipelineFactory.h"
#include "vtkMRMLViewNode.h"
#include "vtkSlicerLayerDMLogic.h"

#include "vtkMRMLModelGlowDisplayNode.h"
#include "vtkMRMLModelGlowPipeline.h"

class VTK_SLICER_MODEL_GLOW_MODULE_MRML_EXPORT vtkMRLMModelGlowLayerDMLogic
{
public:
  static vtkMRMLModelGlowDisplayNode* CreateDisplayNode(vtkMRMLNode* node, bool allowMultiple = false) {
    return vtkSlicerLayerDMLogic::CreateDisplayNode<vtkMRMLModelGlowDisplayNode>(node, allowMultiple);
  }

  static void RegisterPipeline(vtkMRMLScene* scene) {
    static vtkMRMLLayerDMPipelineCreatorI* creator {};
    if (creator) {
      return;
    }

    vtkSlicerLayerDMLogic::RegisterNodeIfNeeded<vtkMRMLModelGlowDisplayNode>(scene);
    auto factory = vtkMRMLLayerDMPipelineFactory::GetInstance();
    creator = factory->AddPipelineCreator(
        [](vtkMRMLAbstractViewNode* viewNode, vtkMRMLNode* displayNode) {
            return layer_dm::TryCreateForView<vtkMRMLViewNode, vtkMRMLModelGlowDisplayNode, vtkMRMLModelGlowPipeline>(viewNode, displayNode);
        }
    );
  }
};
