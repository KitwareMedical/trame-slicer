#include "vtkMRMLModelGlowDisplayNode.h"

// VTK includes
#include <vtkObjectFactory.h>

vtkMRMLNodeNewMacro(vtkMRMLModelGlowDisplayNode);

vtkMRMLModelGlowDisplayNode::vtkMRMLModelGlowDisplayNode()
{
  this->Visibility = false;
}

vtkMRMLModelGlowDisplayNode::~vtkMRMLModelGlowDisplayNode() = default;

void vtkMRMLModelGlowDisplayNode::WriteXML(ostream& of, int nIndent)
{
  Superclass::WriteXML(of, nIndent);
  vtkMRMLWriteXMLBeginMacro(of);
  // vtkMRMLWriteXMLBooleanMacro(IsSelected, IsSelected);
  vtkMRMLWriteXMLEndMacro();
}

void vtkMRMLModelGlowDisplayNode::ReadXMLAttributes(const char** atts)
{
  MRMLNodeModifyBlocker blocker(this);
  Superclass::ReadXMLAttributes(atts);
  vtkMRMLReadXMLBeginMacro(atts);
  // vtkMRMLReadXMLBooleanMacro(isSelected, IsSelected);
  vtkMRMLReadXMLEndMacro();
}

void vtkMRMLModelGlowDisplayNode::Copy(vtkMRMLNode* node)
{
  MRMLNodeModifyBlocker blocker(this);
  Superclass ::CopyContent(node);
  vtkMRMLCopyBeginMacro(node);
  // vtkMRMLCopyBooleanMacro(IsSelected);
  vtkMRMLCopyEndMacro();
}

const char* vtkMRMLModelGlowDisplayNode::GetNodeTagName()
{
  return "ModelGlowDisplay";
}
