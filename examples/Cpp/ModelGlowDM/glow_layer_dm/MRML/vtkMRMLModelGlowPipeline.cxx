#include "vtkMRMLModelGlowPipeline.h"
#include "vtkMRMLModelGlowDisplayNode.h"

// Slicer includes
#include "vtkMRMLInteractionEventData.h"
#include "vtkMRMLModelNode.h"
#include "vtkMRMLTransformNode.h"

// VTK includes
#include <vtkActor.h>
#include "vtkMatrix4x4.h"
#include <vtkObjectFactory.h>
#include <vtkOutlineGlowPass.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindow.h>
#include <vtkRenderer.h>
#include <vtkRenderStepsPass.h>

vtkStandardNewMacro(vtkMRMLModelGlowPipeline);

vtkMRMLModelGlowPipeline::vtkMRMLModelGlowPipeline() = default;
vtkMRMLModelGlowPipeline::~vtkMRMLModelGlowPipeline() = default;

void vtkMRMLModelGlowPipeline::SetDisplayNode(vtkMRMLNode* displayNode)
{
  Superclass::SetDisplayNode(displayNode);

  if (vtkMRMLModelGlowDisplayNode::SafeDownCast(this->GetDisplayNode()))
  {
    this->SetModelNode(vtkMRMLModelNode::SafeDownCast(vtkMRMLModelGlowDisplayNode::SafeDownCast(this->GetDisplayNode())->GetDisplayableNode()));
  }
}

void vtkMRMLModelGlowPipeline::OnRendererRemoved(vtkRenderer* renderer)
{
  if(!renderer || !renderer->HasViewProp(this->GlowActor)) {
    return;
  }
  renderer->RemoveActor(this->GlowActor);
}

void vtkMRMLModelGlowPipeline::OnRendererAdded(vtkRenderer* renderer)
{
  if(!renderer || renderer->HasViewProp(this->GlowActor)) {
    return;
  }
  this->GlowActor->VisibilityOff();
  this->GlowActor->GetProperty()->LightingOff();
  renderer->AddActor(this->GlowActor);

  vtkNew<vtkRenderStepsPass> basicPasses;
  vtkNew<vtkOutlineGlowPass> glowPass;
  glowPass->SetDelegatePass(basicPasses);
  renderer->SetPass(glowPass);
}

void vtkMRMLModelGlowPipeline::UpdatePipeline()
{
  if (this->GetDisplayNode() && this->ModelNode)
  {
    bool visible = vtkMRMLDisplayNode::SafeDownCast(this->GetDisplayNode())->GetVisibility();
    this->GlowActor->SetVisibility(visible);

    double* color = vtkMRMLDisplayNode::SafeDownCast(this->GetDisplayNode())->GetColor();
    this->GlowActor->GetProperty()->SetColor(color);
  }

  RequestRender();
}

void vtkMRMLModelGlowPipeline::SetModelNode(vtkMRMLModelNode* node)
{
  UpdateObserver(this->ModelNode, node);
  this->ModelNode = node;

  if (!this->ModelNode)
  {
    return;
  }

  vtkNew<vtkPolyDataMapper> mapper;
  mapper->SetInputData(this->ModelNode->GetPolyData());
  this->GlowActor->SetMapper(mapper);

  // UpdateObserver(this->ModelNode, node);

  auto transformNode = this->ModelNode->GetParentTransformNode();
  if (transformNode)
  {
    vtkNew<vtkMatrix4x4> userMatrix;
    transformNode->GetMatrixTransformToParent(userMatrix);
    this->GlowActor->SetUserMatrix(userMatrix);
  }
}

void vtkMRMLModelGlowPipeline::OnUpdate(vtkObject* node, unsigned long eventId, void* callData)
{
  if (auto modelNode = vtkMRMLModelNode::SafeDownCast(node))
  {
    SetModelNode(modelNode);
  }

  if (auto displayNode = vtkMRMLModelGlowDisplayNode::SafeDownCast(node))
  {
    SetDisplayNode(displayNode);
  }

  ResetDisplay();
}

bool vtkMRMLModelGlowPipeline::CanProcessInteractionEvent(vtkMRMLInteractionEventData* eventData, double& distance2)
{
  if (!this->GetDisplayNode() || !this->ModelNode)
  {
    return false;
  }

  const double* wp = eventData->GetWorldPosition();
  double* bnds = this->GlowActor->GetBounds();

  bool inBounds = (wp[0] > bnds[0] && wp[0] < bnds[1] && wp[1] > bnds[2] && wp[1] < bnds[3] && wp[2] > bnds[4] && wp[2] < bnds[5]);
  distance2 = vtkMath::Distance2BetweenPoints(wp, this->GlowActor->GetCenter());

  return inBounds;
}

bool vtkMRMLModelGlowPipeline::ProcessInteractionEvent(vtkMRMLInteractionEventData* eventData)
{
  vtkMRMLDisplayNode::SafeDownCast(this->GetDisplayNode())->VisibilityOn();
  return true;
}

void vtkMRMLModelGlowPipeline::LoseFocus(vtkMRMLInteractionEventData* eventData)
{
  vtkMRMLDisplayNode::SafeDownCast(this->GetDisplayNode())->VisibilityOff();
}

unsigned int vtkMRMLModelGlowPipeline::GetRenderOrder() const
{
  return 1000;
}
