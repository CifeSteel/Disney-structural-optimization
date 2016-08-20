﻿Imports SAP2000v16
'Imports Microsoft.Office.Interop.Excel

Module Module1
    Sub Main()
        Dim AppPath = My.Application.Info.DirectoryPath

        Dim sapobj As SapObject = GetObject(, "SAP2000v16.SapObject")
        Dim SM = sapobj.SapModel

        SM.File.OpenFile(AppPath + "\SAPMODEL\delos_turtle.sdb")
        SM.SetPresentUnits(9) 'unit: N,mm,C
        SM.SetModelIsLocked(False)

        'Dim xlapp = New Application
        'xlapp.Visible = 0
        'Dim NodeBK = xlapp.Workbooks.Open(AppPath + "\SAP_I_Node.xlsx")
        'Dim Nodesheet = NodeBK.ActiveSheet
        'Dim NodeNum = Nodesheet.usedrange.rows.count

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

        Dim readstreamnode = New System.IO.StreamReader(AppPath + "\SAP_I_Node.txt", System.Text.Encoding.Default)
        Dim strn1 As String = readstreamnode.ReadLine()
        Do Until readstreamnode.EndOfStream
            Dim nodeinfo As String = readstreamnode.ReadLine()
            Dim nodedata() As String = Split(nodeinfo, ",")
            Node_ID.Add(Convert.ToString(nodedata(0)))
            Node_X.Add(Convert.ToDouble(nodedata(1)))
            Node_Y.Add(Convert.ToDouble(nodedata(2)))
            Node_Z.Add(Convert.ToDouble(nodedata(3)))
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
        Loop
        readstreamnode.Close()

        'For i = 2 To NodeNum
        '    Node_ID.Add(Nodesheet.cells(i, 1).text)
        '    Node_X.Add(Nodesheet.cells(i, 2).value)
        '    Node_Y.Add(Nodesheet.cells(i, 3).value)
        '    Node_Z.Add(Nodesheet.cells(i, 4).value)
        '    Node_memberID.Add(Nodesheet.cells(i, 5).value)
        '    Node_Ground.Add(Nodesheet.cells(i, 6).value)
        '    Node_LoadBearing.Add(Nodesheet.cells(i, 7).value)
        '    Node_U1.Add(Nodesheet.cells(i, 8).value)
        '    Node_U2.Add(Nodesheet.cells(i, 9).value)
        '    Node_U3.Add(Nodesheet.cells(i, 10).value)
        '    Node_R1.Add(Nodesheet.cells(i, 11).value)
        '    Node_R2.Add(Nodesheet.cells(i, 12).value)
        '    Node_R3.Add(Nodesheet.cells(i, 13).value)
        '    Node_Remove.Add(Nodesheet.cells(i, 14).value)
        '    Node_AddBack.Add(Nodesheet.cells(i, 15).value)
        'Next
        'NodeBK.Close()

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

        'Dim MemberBK = xlapp.Workbooks.Open(AppPath + "\SAP_I_Member.xlsx")
        'Dim Membersheet = MemberBK.ActiveSheet
        'Dim MemberNum = Membersheet.usedrange.rows.count

        Dim Member_ID = New List(Of String)
        Dim Member_Start = New List(Of String)
        Dim Member_End = New List(Of String)
        Dim Member_Size = New List(Of String)
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

        Dim readstreammember = New System.IO.StreamReader(AppPath + "\SAP_I_Member.txt", System.Text.Encoding.Default)
        Dim strf1 As String = readstreammember.ReadLine()
        Do Until readstreammember.EndOfStream
            Dim memberinfo As String = readstreammember.ReadLine()
            Dim memberdata() As String = Split(memberinfo, ",")
            Member_ID.Add(Convert.ToString(memberdata(0)))
            Member_Start.Add(Convert.ToString(memberdata(1)))
            Member_End.Add(Convert.ToString(memberdata(2)))
            Member_Size.Add(Convert.ToString(memberdata(3)))
            Member_I_U1.Add(Convert.ToBoolean(memberdata(4)))
            Member_I_U2.Add(Convert.ToBoolean(memberdata(5)))
            Member_I_U3.Add(Convert.ToBoolean(memberdata(6)))
            Member_I_R1.Add(Convert.ToBoolean(memberdata(7)))
            Member_I_R2.Add(Convert.ToBoolean(memberdata(8)))
            Member_I_R3.Add(Convert.ToBoolean(memberdata(9)))
            Member_J_U1.Add(Convert.ToBoolean(memberdata(10)))
            Member_J_U2.Add(Convert.ToBoolean(memberdata(11)))
            Member_J_U3.Add(Convert.ToBoolean(memberdata(12)))
            Member_J_R1.Add(Convert.ToBoolean(memberdata(13)))
            Member_J_R2.Add(Convert.ToBoolean(memberdata(14)))
            Member_J_R3.Add(Convert.ToBoolean(memberdata(15)))
            Member_AddBack.Add(Convert.ToBoolean(memberdata(16)))
        Loop
        readstreammember.Close()

        'For i = 2 To MemberNum
        '    Member_ID.Add(Membersheet.cells(i, 1).text)
        '    Member_Start.Add(Membersheet.cells(i, 2).text)
        '    Member_End.Add(Membersheet.cells(i, 3).text)
        '    Member_Size.Add(Membersheet.cells(i, 4).text)
        '    Member_I_U1.Add(Membersheet.cells(i, 5).value)
        '    Member_I_U2.Add(Membersheet.cells(i, 6).value)
        '    Member_I_U3.Add(Membersheet.cells(i, 7).value)
        '    Member_I_R1.Add(Membersheet.cells(i, 8).value)
        '    Member_I_R2.Add(Membersheet.cells(i, 9).value)
        '    Member_I_R3.Add(Membersheet.cells(i, 10).value)
        '    Member_J_U1.Add(Membersheet.cells(i, 11).value)
        '    Member_J_U2.Add(Membersheet.cells(i, 12).value)
        '    Member_J_U3.Add(Membersheet.cells(i, 13).value)
        '    Member_J_R1.Add(Membersheet.cells(i, 14).value)
        '    Member_J_R2.Add(Membersheet.cells(i, 15).value)
        '    Member_J_R3.Add(Membersheet.cells(i, 16).value)
        '    Member_AddBack.Add(Membersheet.cells(i, 17).value)
        'Next
        'MemberBK.Close()

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

            If Member_Size(i) = "0" Then
                SM.FrameObj.Delete(Member_ID(i)) 'remove members
            Else
                memberlist.Add(i) 'count members
            End If

        Next i
        SM.View.RefreshView(0, False)


        SM.File.Save(AppPath + "\SAPMODEL\delos_turtle.sdb")

        Dim time As String = (Int(Now.Year) * 10 ^ 10 + Int(Now.Month) * 10 ^ 8 + Int(Now.Day) * 10 ^ 6 + Int(Now.Hour) * 10 ^ 4 + Int(Now.Minute) * 10 ^ 2 + Int(Now.Second)).ToString
        SM.File.Save(AppPath + "\SAPMODEL\delos_turtle_" + time + ".sdb")



        SM.Analyze.RunAnalysis()
        SM.DesignSteel.StartDesign()



        Dim numberitems As Integer
        Dim rfname() As String = {}
        Dim ratio() As Double = {}
        Dim ratiotype() As Integer = {}
        Dim location() As Double = {}
        Dim comboname() As String = {}
        Dim errorsummary() As String = {}
        Dim warningsummary() As String = {}

        Dim NumberResults As Integer
        Dim obj() As String = {}
        Dim objsta() As Double = {}
        Dim elm() As String = {}
        Dim ElmSta() As Double = {}
        Dim LoadCase() As String = {}
        Dim StepType() As String = {}
        Dim StepNum() As Double = {}
        Dim P() As Double = {}
        Dim V2() As Double = {}
        Dim V3() As Double = {}
        Dim T() As Double = {}
        Dim M2() As Double = {}
        Dim M3() As Double = {}

        'Dim MemberForcebook As Workbook = xlapp.Workbooks.Add
        'Dim MemberForcesheet = MemberForcebook.ActiveSheet
        'MemberForcesheet.Cells(1, 1).Value = "member_ID"
        'MemberForcesheet.cells(1, 2).Value = "Start_Node"
        'MemberForcesheet.cells(1, 3).Value = "End_Node"
        'MemberForcesheet.Cells(1, 4).Value = "Governing_Load_Case"
        'MemberForcesheet.Cells(1, 5).Value = "P"
        'MemberForcesheet.Cells(1, 6).Value = "Mx"
        'MemberForcesheet.Cells(1, 7).Value = "My"
        'MemberForcesheet.cells(1, 8).value = "DC_Ratio"

        Dim memberforce = New System.IO.StreamWriter(AppPath + "\SAP_O_MemberForce.txt", False)
        Dim memberforce1 As String = "member_ID,Start_Node,End_Node,Governing_Load_Case,P,Mx,My,DC_Ratio"
        memberforce.WriteLine(memberforce1)

        For i = 0 To memberlist.Count - 1
            SM.DesignSteel.GetSummaryResults(Member_ID(memberlist(i)), numberitems, rfname, ratio, ratiotype, location, comboname, errorsummary, warningsummary)
            'MemberForcesheet.cells(i + 2, 1).value = Member_ID(memberlist(i))
            'MemberForcesheet.cells(i + 2, 2).value = Member_Start(memberlist(i))
            'MemberForcesheet.cells(i + 2, 3).value = Member_End(memberlist(i))
            'MemberForcesheet.cells(i + 2, 4).value = comboname(0)
            'MemberForcesheet.Cells(i + 2, 8).value = ratio

            SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
            SM.Results.Setup.SetComboSelectedForOutput(comboname(0))
            SM.Results.FrameForce(Member_ID(memberlist(i)), 0, NumberResults, obj, objsta, elm, ElmSta, LoadCase, StepType, StepNum, P, V2, V3, T, M2, M3)
            Dim maxP As Double = P(0)
            Dim maxM2 As Double = M2(0)
            Dim maxM3 As Double = M3(0)
            For j = 1 To NumberResults - 1
                If Math.Abs(P(j)) > Math.Abs(maxP) Then
                    maxP = P(j)
                End If
                If Math.Abs(M2(j)) > Math.Abs(maxM2) Then
                    maxM2 = M2(j)
                End If
                If Math.Abs(M3(j)) > Math.Abs(maxM3) Then
                    maxM3 = M3(j)
                End If
            Next
            'MemberForcesheet.cells(i + 2, 5).value = maxP
            'MemberForcesheet.cells(i + 2, 6).value = maxM2
            'MemberForcesheet.cells(i + 2, 7).value = maxM3

            Dim line As String = Member_ID(memberlist(i)) & "," & Member_Start(memberlist(i)) & "," & Member_End(memberlist(i)) & "," & comboname(0) & "," & maxP & "," & maxM2 & "," & maxM3 & "," & ratio(0)
            memberforce.WriteLine(line)
        Next
        memberforce.Close()

        'xlapp.DisplayAlerts = False
        'MemberForcebook.SaveAs(AppPath + "\SAP_O_MemberForce.csv", 6)
        'MemberForcebook.Close()


        'Dim Modebook As Workbook = xlapp.Workbooks.Add
        'Dim ModeSheet = Modebook.ActiveSheet
        'ModeSheet.cells(1, 1).value = "Mode"
        'ModeSheet.cells(1, 2).value = "Frequency"
        Dim Period() As Double = {}
        Dim Frequency() As Double = {}
        Dim CircFreq() As Double = {}
        Dim EigenValue() As Double = {}

        Dim modefrequency = New System.IO.StreamWriter(AppPath + "\SAP_O_ModeFrequency.txt", False)
        Dim modefrequency1 As String = "Mode,Frequency"
        modefrequency.WriteLine(modefrequency1)

        SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
        SM.Results.Setup.SetCaseSelectedForOutput("MODAL")
        SM.Results.ModalPeriod(NumberResults, LoadCase, StepType, StepNum, Period, Frequency, CircFreq, EigenValue)
        For i = 1 To NumberResults
            'ModeSheet.cells(i + 1, 1).value = i
            'ModeSheet.cells(i + 1, 2).value = Frequency(i - 1)
            Dim line As String = i & "," & Frequency(i - 1)
            modefrequency.WriteLine(line)
        Next i
        modefrequency.Close()
        'xlapp.DisplayAlerts = False
        'Modebook.SaveAs(AppPath + "\SAP_O_ModeFrequency.csv", 6)
        'Modebook.Close()


        Dim NumberNames As Integer
        Dim MyName() As String = {}
        SM.RespCombo.GetNameList(NumberNames, MyName)

        'Dim NodeForcebook As Workbook = xlapp.Workbooks.Add
        'Dim nodeforcesheet = NodeForcebook.ActiveSheet
        'nodeforcesheet.cells(1, 1).value = "Node_ID"
        'nodeforcesheet.CELLS(1, 2).VALUE = "Member_ID"
        'nodeforcesheet.cells(1, 3).value = "Section"
        'nodeforcesheet.cells(1, 4).value = "Load_Combination"
        'nodeforcesheet.cells(1, 5).value = "vertical_reaction_at_Column_Base"
        'nodeforcesheet.cells(1, 6).value = "horizontal_reaction_x_at_Column_Base"
        'nodeforcesheet.cells(1, 7).value = "horizontal_reaction_y_at_Column_Base"
        Dim F1() As Double = {}
        Dim F2() As Double = {}
        Dim F3() As Double = {}
        Dim M1() As Double = {}

        Dim nodeforce = New System.IO.StreamWriter(AppPath + "\SAP_O_NodeForce.txt", False)
        Dim nodeforce1 As String = "Node_ID,Member_ID,Section,Load_Combination,vertical_reaction_at_Column_Base,horizontal_reaction_x_at_Column_Base,horizontal_reaction_y_at_Column_Base"
        nodeforce.WriteLine(nodeforce1)
        Dim sec0 As String
        For i = 0 To nodelist.Count - 1
            'nodeforcesheet.cells(i + 2, 1).value = Node_ID(nodelist(i))
            'nodeforcesheet.cells(i + 2, 2).value = Node_memberID(nodelist(i))

            'If Node_memberID(nodelist(i)) <> "0" Then
            '    nodeforcesheet.cells(i + 2, 3).value = Member_Size(Member_ID.IndexOf(Node_memberID(nodelist(i))))
            'Else
            '    nodeforcesheet.cells(i + 2, 3).value = "0"
            'End If

            If Node_memberID(nodelist(i)) <> "0" Then
                sec0 = Member_Size(Member_ID.IndexOf(Node_memberID(nodelist(i))))
            Else
                sec0 = "0"
            End If

            Dim line As String = Node_ID(nodelist(i)) & "," & Node_memberID(nodelist(i)) & "," & sec0
            'For j = 0 To NumberNames - 1
            '    SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
            '    SM.Results.Setup.SetComboSelectedForOutput(MyName(j))
            '    SM.Results.JointReact(Node_ID(nodelist(i)), 0, NumberResults, obj, elm, LoadCase, StepType, StepNum, F1, F2, F3, M1, M2, M3)
            '    nodeforcesheet.cells(i + 2, 4 + 4 * j).value = MyName(j)
            '    nodeforcesheet.cells(i + 2, 5 + 4 * j).value = F3
            '    nodeforcesheet.cells(i + 2, 6 + 4 * j).value = F1
            '    nodeforcesheet.cells(i + 2, 7 + 4 * j).value = F2
            'Next

            For j = 0 To NumberNames - 1
                'For j = 0 To NumberNames - 1

                SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
                SM.Results.Setup.SetComboSelectedForOutput(MyName(j))
                SM.Results.JointReact(Node_ID(nodelist(i)), 0, NumberResults, obj, elm, LoadCase, StepType, StepNum, F1, F2, F3, M1, M2, M3)

                If F1.Length <> 0 Then
                    line = line & "," & MyName(j) & "," & F3(0) & "," & F1(0) & "," & F2(0)
                End If


                'nodeforcesheet.cells(i + 2, 4 + 4 * j).value = MyName(j)
                'nodeforcesheet.cells(i + 2, 5 + 4 * j).value = F3
                'nodeforcesheet.cells(i + 2, 6 + 4 * j).value = F1
                'nodeforcesheet.cells(i + 2, 7 + 4 * j).value = F2
            Next
            nodeforce.WriteLine(line)
        Next
        nodeforce.Close()
        'xlapp.DisplayAlerts = False
        'NodeForcebook.SaveAs(AppPath + "\SAP_O_NodeForce.csv", 6)
        'NodeForcebook.Close()


        Dim jointdispl = New System.IO.StreamWriter(AppPath + "\SAP_O_NodeDisplacement.txt", False)
        Dim jointdispl1 As String = "Node_ID,Load_Combination,u1,u2,u3,r1,r2,r3"
        jointdispl.WriteLine(jointdispl1)
        Dim u1() As Double = {}
        Dim u2() As Double = {}
        Dim u3() As Double = {}
        Dim r1() As Double = {}
        Dim r2() As Double = {}
        Dim r3() As Double = {}
        For i = 0 To Node_ID_new.Count - 1
            Dim line As String = Node_ID_new(i)
            For j = 0 To 0
                SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
                SM.Results.Setup.SetComboSelectedForOutput(MyName(j))
                SM.Results.JointDispl(Node_ID_new(i), 0, NumberResults, obj, elm, LoadCase, StepType, StepNum, u1, u2, u3, r1, r2, r3)

                If u1.Length <> 0 Then
                    line = line & "," & MyName(j) & "," & u1(0) & "," & u2(0) & "," & u3(0) & "," & r1(0) & "," & r2(0) & "," & r3(0)
                End If

                'nodeforcesheet.cells(i + 2, 4 + 4 * j).value = MyName(j)
                'nodeforcesheet.cells(i + 2, 5 + 4 * j).value = F3
                'nodeforcesheet.cells(i + 2, 6 + 4 * j).value = F1
                'nodeforcesheet.cells(i + 2, 7 + 4 * j).value = F2
            Next
            jointdispl.WriteLine(line)
        Next
        jointdispl.Close()


        'xlapp.Quit()
    End Sub
End Module
