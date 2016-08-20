﻿Imports SAP2000v16
'Imports Microsoft.Office.Interop.Excel

Module SpacePacking

    Function distance(ByVal ax As Double, ByVal ay As Double, ByVal az As Double, ByVal bx As Double, ByVal by As Double, ByVal bz As Double) As Double
        Return ((ax - bx) ^ 2 + (ay - by) ^ 2 + (az - bz) ^ 2) ^ 0.5
    End Function


    Sub Main()
        Dim AppPath = My.Application.Info.DirectoryPath

        Dim sapobj As SapObject = GetObject(, "SAP2000v16.SapObject")
        Dim SM = sapobj.SapModel

        SM.File.OpenFile(AppPath + "\SAPMODEL\delos_turtle.sdb")
        SM.SetPresentUnits(9) 'unit: N,mm,C
        SM.SetModelIsLocked(False)

        Dim Node_ID = New List(Of String)
        Dim Node_X = New List(Of Double)
        Dim Node_Y = New List(Of Double)
        Dim Node_Z = New List(Of Double)
        Dim Node_memberID = New List(Of String)
        Dim Node_Ground = New List(Of Boolean)
        Dim Node_LoadBearing = New List(Of Boolean)
        Dim Node_U1 = New List(Of Boolean)
        Dim Node_U2 = New List(Of Boolean)
        Dim Node_U3 = New List(Of Boolean)
        Dim Node_R1 = New List(Of Boolean)
        Dim Node_R2 = New List(Of Boolean)
        Dim Node_R3 = New List(Of Boolean)
        Dim Node_Remove = New List(Of Boolean)
        Dim Node_AddBack = New List(Of Boolean)
        Dim Node_ID_new = New List(Of String)

        Dim Dic_Node As New Dictionary(Of String, String)
        Dim toggle As Boolean
        Dim ptsp As Integer


        Dim readstreamnode = New System.IO.StreamReader(AppPath + "\RH_OUTPUT_SP_NODES.csv", System.Text.Encoding.Default)
        Dim strn1 As String = readstreamnode.ReadLine()

        Do Until readstreamnode.EndOfStream

            Dim nodeinfo As String = readstreamnode.ReadLine()
            Dim nodedata() As String = Split(nodeinfo, ",")

            Dim xx = Math.Round(Convert.ToDouble(nodedata(1)), 5)
            Dim yy = Math.Round(Convert.ToDouble(nodedata(2)), 5)
            Dim zz = Math.Round(Convert.ToDouble(nodedata(3)), 5)

            For k As Integer = 0 To Node_ID.Count - 1
                If distance(Node_X(k), Node_Y(k), Node_Z(k), xx, yy, zz) <= 1 Then
                    toggle = True
                    ptsp = k
                    Exit For
                Else
                    toggle = False
                End If
            Next

            If toggle Then 'repeated
                Dic_Node.Add(Convert.ToString(nodedata(0)), Node_ID(ptsp))
            Else
                Dic_Node.Add(Convert.ToString(nodedata(0)), Convert.ToString(nodedata(0)))
                Node_ID.Add(Convert.ToString(nodedata(0)))
                Node_X.Add(xx)
                Node_Y.Add(yy)
                Node_Z.Add(zz)
                Node_memberID.Add(Convert.ToString(nodedata(4)))
                Node_Ground.Add(Convert.ToBoolean(nodedata(5)))
                Node_LoadBearing.Add(Convert.ToBoolean(nodedata(6)))
                Node_U1.Add(Convert.ToBoolean(nodedata(7)))
                Node_U2.Add(Convert.ToBoolean(nodedata(8)))
                Node_U3.Add(Convert.ToBoolean(nodedata(9)))
                Node_R1.Add(Convert.ToBoolean(nodedata(10)))
                Node_R2.Add(Convert.ToBoolean(nodedata(11)))
                Node_R3.Add(Convert.ToBoolean(nodedata(12)))
                Node_Remove.Add(Convert.ToBoolean(nodedata(13)))
                Node_AddBack.Add(Convert.ToBoolean(nodedata(14)))
            End If

        Loop
        readstreamnode.Close()

        Dim pname As String = ""
        Dim Value() As Boolean
        Dim nodelist = New List(Of Integer)

        For i = 0 To Node_ID.Count - 1

            If Node_AddBack(i) = True Then
                SM.PointObj.AddCartesian(Node_X(i), Node_Y(i), Node_Z(i), pname, Node_ID(i)) 'create 'add back' nodes
            End If

            Value = {Node_U1(i), Node_U2(i), Node_U3(i), Node_R1(i), Node_R2(i), Node_R3(i)}
            SM.PointObj.SetRestraint(Node_ID(i), Value)   'reset restraint

            If Node_Remove(i) = True Then
                SM.PointObj.DeleteSpecialPoint(Node_ID(i)) 'remove nodes
            Else
                Node_ID_new.Add(Node_ID(i))
            End If

            If Node_Ground(i) = True Then
                nodelist.Add(i) 'count ground nodes
            End If
        Next
        SM.View.RefreshView(0, False)

        Dim Member_ID = New List(Of String)
        Dim Member_Start = New List(Of String)
        Dim Member_End = New List(Of String)
        Dim Member_Size = New List(Of String)
        Dim Member_Orientation = New List(Of Double)
        Dim Member_I_U1 = New List(Of Boolean)
        Dim Member_I_U2 = New List(Of Boolean)
        Dim Member_I_U3 = New List(Of Boolean)
        Dim Member_I_R1 = New List(Of Boolean)
        Dim Member_I_R2 = New List(Of Boolean)
        Dim Member_I_R3 = New List(Of Boolean)
        Dim Member_J_U1 = New List(Of Boolean)
        Dim Member_J_U2 = New List(Of Boolean)
        Dim Member_J_U3 = New List(Of Boolean)
        Dim Member_J_R1 = New List(Of Boolean)
        Dim Member_J_R2 = New List(Of Boolean)
        Dim Member_J_R3 = New List(Of Boolean)
        Dim Member_AddBack = New List(Of Boolean)

        Dim readstreammember = New System.IO.StreamReader(AppPath + "\RH_OUTPUT_SP_MEMBERS.csv", System.Text.Encoding.Default)
        Dim strf1 As String = readstreammember.ReadLine()
        Do Until readstreammember.EndOfStream
            Dim memberinfo As String = readstreammember.ReadLine()
            Dim memberdata() As String = Split(memberinfo, ",")
            Member_ID.Add(Convert.ToString(memberdata(0)))
            Member_Start.Add(Dic_Node(Convert.ToString(memberdata(1))))
            Member_End.Add(Dic_Node(Convert.ToString(memberdata(2))))
            Member_Size.Add(Convert.ToString(memberdata(3)))
            Member_Orientation.Add(Convert.ToDouble(memberdata(4)))
            Member_I_U1.Add(Convert.ToBoolean(memberdata(5)))
            Member_I_U2.Add(Convert.ToBoolean(memberdata(6)))
            Member_I_U3.Add(Convert.ToBoolean(memberdata(7)))
            Member_I_R1.Add(Convert.ToBoolean(memberdata(8)))
            Member_I_R2.Add(Convert.ToBoolean(memberdata(9)))
            Member_I_R3.Add(Convert.ToBoolean(memberdata(10)))
            Member_J_U1.Add(Convert.ToBoolean(memberdata(11)))
            Member_J_U2.Add(Convert.ToBoolean(memberdata(12)))
            Member_J_U3.Add(Convert.ToBoolean(memberdata(13)))
            Member_J_R1.Add(Convert.ToBoolean(memberdata(14)))
            Member_J_R2.Add(Convert.ToBoolean(memberdata(15)))
            Member_J_R3.Add(Convert.ToBoolean(memberdata(16)))
            Member_AddBack.Add(Convert.ToBoolean(memberdata(17)))
        Loop
        readstreammember.Close()

        Dim framename As String = ""
        Dim ii() As Boolean = {}
        Dim jj() As Boolean = {}
        Dim Startvalue() As Double = {}
        Dim EndValue() As Double = {}
        Dim memberlist = New List(Of Integer)

        For i = 0 To Member_ID.Count - 1

            If Member_AddBack(i) = True Then
                SM.FrameObj.AddByPoint(Member_Start(i), Member_End(i), framename, Member_Size(i), Member_ID(i)) 'create 'add back' members
            Else
                SM.FrameObj.SetSection(Member_ID(i), Member_Size(i)) 'update section sizes
            End If
            ii = {Member_I_U1(i), Member_I_U2(i), Member_I_U3(i), Member_I_R1(i), Member_I_R2(i), Member_I_R3(i)}
            jj = {Member_J_U1(i), Member_J_U2(i), Member_J_U3(i), Member_J_R1(i), Member_J_R2(i), Member_J_R3(i)}
            SM.FrameObj.SetReleases(Member_ID(i), ii, jj, Startvalue, EndValue) 'reset releases
            SM.FrameObj.SetLocalAxes(Member_ID(i), Member_Orientation(i))

            If Member_Size(i) = "0" Then
                SM.FrameObj.Delete(Member_ID(i)) 'remove members
            Else
                memberlist.Add(i) 'count members
            End If

        Next i
        SM.View.RefreshView(0, False)


        Dim readstreamt = New System.IO.StreamReader(AppPath + "\RH_OUTPUT_TAB_KICKER.csv", System.Text.Encoding.Default)
        Dim strt1 As String = readstreamt.ReadLine()

        Do Until readstreamt.EndOfStream

            Dim tinfo As String = readstreamt.ReadLine()
            Dim tdata() As String = Split(tinfo, ",")

            Dim tx = Math.Round(Convert.ToDouble(tdata(4)), 5)
            Dim ty = Math.Round(Convert.ToDouble(tdata(5)), 5)
            Dim tz = Math.Round(Convert.ToDouble(tdata(6)), 5)

            For k As Integer = 0 To Node_ID.Count - 1
                If distance(Node_X(k), Node_Y(k), Node_Z(k), tx, ty, tz) <= 1 Then
                    toggle = True
                    ptsp = k
                    Exit For
                Else
                    toggle = False
                End If
            Next

            If toggle Then 'repeated
                Dic_Node.Add(Convert.ToString(tdata(3)), Node_ID(ptsp))
            Else
                Dic_Node.Add(Convert.ToString(tdata(3)), Convert.ToString(tdata(3)))
                Node_ID.Add(Convert.ToString(tdata(3)))
                Node_X.Add(tx)
                Node_Y.Add(ty)
                Node_Z.Add(tz)
            End If

        Loop
        readstreamt.Close()


        Dim readstreamk = New System.IO.StreamReader(AppPath + "\RH_OUTPUT_TAB_KICKER.csv", System.Text.Encoding.Default)
        Dim strk1 As String = readstreamk.ReadLine()

        Do Until readstreamk.EndOfStream

            Dim kinfo As String = readstreamk.ReadLine()
            Dim kdata() As String = Split(kinfo, ",")

            If Convert.ToString(kdata(13)) = "NONE" Then
                Continue Do
            End If

            Dim kx = Math.Round(Convert.ToDouble(kdata(14)), 5)
            Dim ky = Math.Round(Convert.ToDouble(kdata(15)), 5)
            Dim kz = Math.Round(Convert.ToDouble(kdata(16)), 5)

            For k As Integer = 0 To Node_ID.Count - 1
                If distance(Node_X(k), Node_Y(k), Node_Z(k), kx, ky, kz) <= 1 Then
                    toggle = True
                    ptsp = k
                    Exit For
                Else
                    toggle = False
                End If
            Next

            If toggle Then 'repeated
                Dic_Node.Add(Convert.ToString(kdata(13)), Node_ID(ptsp))
            Else
                Dic_Node.Add(Convert.ToString(kdata(13)), Convert.ToString(kdata(13)))
                Node_ID.Add(Convert.ToString(kdata(13)))
                Node_X.Add(kx)
                Node_Y.Add(ky)
                Node_Z.Add(kz)
            End If

        Loop
        readstreamk.Close()


        Dim dicnode = New System.IO.StreamWriter(AppPath + "\Dictionary_nodes.txt", False)
        Dim dicnode1 As String = "original_name,existing_node"
        dicnode.WriteLine(dicnode1)

        For Each pair In Dic_Node
            Dim line As String = pair.Key & "," & pair.Value
            dicnode.WriteLine(line)
        Next
        dicnode.Close()




        SM.File.Save(AppPath + "\SAPMODEL\delos_turtle.sdb")

        Dim time As String = (Int(Now.Year) * 10 ^ 10 + Int(Now.Month) * 10 ^ 8 + Int(Now.Day) * 10 ^ 6 + Int(Now.Hour) * 10 ^ 4 + Int(Now.Minute) * 10 ^ 2 + Int(Now.Second)).ToString
        SM.File.Save(AppPath + "\SAPMODEL\delos_turtle" + time + ".sdb")


    End Sub

End Module
