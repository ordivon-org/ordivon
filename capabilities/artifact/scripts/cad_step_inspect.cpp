#include <STEPControl_Reader.hxx>
#include <IFSelect_ReturnStatus.hxx>
#include <TopoDS_Shape.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <Bnd_Box.hxx>
#include <BRepBndLib.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <iostream>
#include <iomanip>

static int uniqueCount(const TopoDS_Shape& shape, TopAbs_ShapeEnum kind) {
  TopTools_IndexedMapOfShape map;
  TopExp::MapShapes(shape, kind, map);
  return map.Extent();
}

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "usage: cad_step_inspect file.step\n";
    return 64;
  }
  STEPControl_Reader reader;
  IFSelect_ReturnStatus read_status = reader.ReadFile(argv[1]);
  if (read_status != IFSelect_RetDone) {
    std::cout << "{\"status\":\"FAIL\",\"stage\":\"read\",\"readStatus\":" << static_cast<int>(read_status) << "}\n";
    return 2;
  }
  int roots = reader.NbRootsForTransfer();
  int transferred = reader.TransferRoots();
  TopoDS_Shape shape = reader.OneShape();
  if (shape.IsNull()) {
    std::cout << "{\"status\":\"FAIL\",\"stage\":\"transfer\",\"roots\":" << roots << ",\"transferred\":" << transferred << "}\n";
    return 3;
  }
  BRepCheck_Analyzer analyzer(shape, true);
  Bnd_Box box;
  BRepBndLib::Add(shape, box, false);
  Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
  box.Get(xmin, ymin, zmin, xmax, ymax, zmax);
  GProp_GProps volume_properties;
  BRepGProp::VolumeProperties(shape, volume_properties);
  GProp_GProps surface_properties;
  BRepGProp::SurfaceProperties(shape, surface_properties);
  std::cout << std::setprecision(15)
            << "{\"status\":\"PASS\",\"readStatus\":" << static_cast<int>(read_status)
            << ",\"roots\":" << roots
            << ",\"transferred\":" << transferred
            << ",\"valid\":" << (analyzer.IsValid() ? "true" : "false")
            << ",\"solids\":" << uniqueCount(shape, TopAbs_SOLID)
            << ",\"faces\":" << uniqueCount(shape, TopAbs_FACE)
            << ",\"edges\":" << uniqueCount(shape, TopAbs_EDGE)
            << ",\"volumeMm3\":" << volume_properties.Mass()
            << ",\"areaMm2\":" << surface_properties.Mass()
            << ",\"bboxMm\":{\"xmin\":" << xmin
            << ",\"ymin\":" << ymin
            << ",\"zmin\":" << zmin
            << ",\"xmax\":" << xmax
            << ",\"ymax\":" << ymax
            << ",\"zmax\":" << zmax << "}}\n";
  return analyzer.IsValid() ? 0 : 4;
}
