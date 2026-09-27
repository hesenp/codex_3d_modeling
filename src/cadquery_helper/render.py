"""Headless, depth-buffered previews from CAD tessellation using VTK/EGL."""

from pathlib import Path

import cadquery as cq
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from cadquery_helper.models import as_shape, inspect_shape


def render_model(
    model: cq.Workplane | cq.Shape,
    output: Path,
    title: str = "CadQuery model",
    cutaway: bool = False,
) -> Path:
    shape = as_shape(model)
    info = inspect_shape(shape)
    low, high = np.array(info["min_mm"]), np.array(info["max_mm"])
    center = (low + high) / 2
    span = max(high - low)
    if cutaway:
        # Keep the rear half (Y >= midpoint) to expose the wall/base section.
        clipping_box = (
            cq.Workplane("XY")
            .box(span * 3, span * 2, span * 3)
            .translate((center[0], center[1] + span, center[2]))
        )
        shape = shape.intersect(clipping_box.val())
        title += " - cutaway at mid-Y"
    vertices, triangles = shape.tessellate(0.02, 0.1)
    if not triangles:
        raise ValueError("Model has no renderable faces")
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.array([point.toTuple() for point in vertices]), deep=True))
    cells = vtk.vtkCellArray()
    for triangle in triangles:
        cells.InsertNextCell(3, triangle)
    mesh = vtk.vtkPolyData()
    mesh.SetPoints(points)
    mesh.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(mesh)
    normals.ComputePointNormalsOff()
    normals.ComputeCellNormalsOn()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.ScalarVisibilityOff()

    # EGL works without DISPLAY on this Linux host, including software Mesa.
    # A depth buffer is important: painter-sorted triangles misrender thin walls.
    window = vtk.vtkEGLRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(2400, 880)
    window.SetMultiSamples(4)
    window.SetNumberOfLayers(2)
    background = vtk.vtkRenderer()
    background.SetBackground(0.957, 0.965, 0.973)
    window.AddRenderer(background)
    views = [((1.4, -1.8, 1.3), (0, 0, 1), "Isometric"),
             ((0, 0, 3), (0, 1, 0), "Top - XY"),
             ((0, -3, 0), (0, 0, 1), "Front - XZ")]
    for index, (direction, up, _) in enumerate(views):
        renderer = vtk.vtkRenderer()
        renderer.SetViewport(index / 3, 0.13, (index + 1) / 3, 0.83)
        renderer.SetBackground(0.957, 0.965, 0.973)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.30, 0.64, 0.73)
        actor.GetProperty().SetInterpolationToFlat()
        actor.GetProperty().SetAmbient(0.3)
        actor.GetProperty().SetDiffuse(0.7)
        renderer.AddActor(actor)
        camera = renderer.GetActiveCamera()
        camera.SetFocalPoint(*center)
        camera.SetPosition(*(center + np.array(direction) * span))
        camera.SetViewUp(*up)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(span * (0.82 if index == 0 else 0.63))
        renderer.ResetCameraClippingRange()
        window.AddRenderer(renderer)

    # Text overlay is kept separate from the three model cameras.
    overlay = vtk.vtkRenderer()
    overlay.SetLayer(1)
    overlay.InteractiveOff()
    window.AddRenderer(overlay)

    def label(text: str, x: int, y: int, size: int) -> None:
        actor = vtk.vtkTextActor()
        actor.SetInput(text)
        actor.SetDisplayPosition(x, y)
        style = actor.GetTextProperty()
        style.SetFontSize(size)
        style.SetColor(0.13, 0.23, 0.29)
        style.SetJustificationToCentered()
        overlay.AddViewProp(actor)

    label(title, 1200, 816, 32)
    for index, (_, _, name) in enumerate(views):
        label(name, index * 800 + 400, 751, 24)
    dimensions = " x ".join(f"{value:g}" for value in info["size_mm"])
    label(f"Outer dimensions: {dimensions} mm  |  CAD-derived orthographic views", 1200, 42, 23)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        window.Render()
        capture = vtk.vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.ReadFrontBufferOff()
        capture.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(output))
        writer.SetInputConnection(capture.GetOutputPort())
        writer.Write()
        if writer.GetErrorCode() or not output.is_file():
            raise RuntimeError(f"Could not render {output}")
    finally:
        window.Finalize()
    return output
