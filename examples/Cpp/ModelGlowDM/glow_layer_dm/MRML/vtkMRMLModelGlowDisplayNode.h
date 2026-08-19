#pragma once

#include "vtkSlicerModelGlowModuleMRMLModule.h"

// Slicer includes
#include "vtkMRMLModelDisplayNode.h"
#include "vtkSlicerLayerDMLogic.h"


class VTK_SLICER_MODEL_GLOW_MODULE_MRML_EXPORT vtkMRMLModelGlowDisplayNode : public vtkMRMLDisplayNode
{
public:
  static vtkMRMLModelGlowDisplayNode* New();
  vtkTypeMacro(vtkMRMLModelGlowDisplayNode, vtkMRMLDisplayNode);

  void WriteXML(ostream& of, int nIndent) override;
  void ReadXMLAttributes(const char** atts) override;
  void Copy(vtkMRMLNode* node) override;

  vtkMRMLNode* CreateNodeInstance() override;
  const char* GetNodeTagName() override;

  // vtkGetMacro(IsSelected, bool);
  // vtkSetMacro(IsSelected, bool);

protected:
  vtkMRMLModelGlowDisplayNode();
  ~vtkMRMLModelGlowDisplayNode() override;

  vtkMRMLModelGlowDisplayNode(const vtkMRMLModelGlowDisplayNode&) = delete;
  void operator=(const vtkMRMLModelGlowDisplayNode&) = delete;

  // bool IsSelected{};
};
