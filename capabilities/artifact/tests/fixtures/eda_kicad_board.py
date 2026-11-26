"""Native KiCad package-owned Python fixture generator."""

import argparse
from pathlib import Path


def make_board(path: Path, *, bad: bool) -> None:
    import pcbnew

    def mm(x):
        return pcbnew.FromMM(x)

    def v(x, y):
        return pcbnew.VECTOR2I(mm(x), mm(y))

    board = pcbnew.BOARD()
    for a, b in [((0, 0), (40, 0)), ((40, 0), (40, 30)), ((40, 30), (0, 30)), ((0, 30), (0, 0))]:
        shape = pcbnew.PCB_SHAPE(board)
        shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetStart(v(*a))
        shape.SetEnd(v(*b))
        shape.SetLayer(pcbnew.Edge_Cuts)
        shape.SetWidth(mm(0.2))
        board.Add(shape)
    for ref, x, net_name, code in [("J1", 10.0, "N1", 1), ("J2", 10.7 if bad else 30.0, "N2", 2)]:
        net = pcbnew.NETINFO_ITEM(board, net_name, code)
        board.Add(net)
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(ref)
        fp.SetValue("TEST")
        fp.SetPosition(v(x, 15))
        board.Add(fp)
        pad = pcbnew.PAD(fp)
        pad.SetNumber("1")
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(v(2, 2))
        pad.SetDrillSize(v(1, 1))
        pad.SetPosition(v(x, 15))
        pad.SetNet(net)
        fp.Add(pad)
    pcbnew.SaveBoard(str(path), board)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--bad", action="store_true")
    args = parser.parse_args()
    make_board(args.path, bad=args.bad)
