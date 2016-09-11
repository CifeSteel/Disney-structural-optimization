Imports SAP2000v16

Module Module1
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

        Dim memberforce = New System.IO.StreamWriter(AppPath + "\SAP_O_MemberForce.txt", False)
        Dim memberforce1 As String = "member_ID,Start_Node,End_Node,Governing_Load_Case,P,Mx,My,DC_Ratio"
        memberforce.WriteLine(memberforce1)

        For i = 0 To memberlist.Count - 1
            SM.DesignSteel.GetSummaryResults(Member_ID(memberlist(i)), numberitems, rfname, ratio, ratiotype, location, comboname, errorsummary, warningsummary)

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

            Dim line As String = Member_ID(memberlist(i)) & "," & Member_Start(memberlist(i)) & "," & Member_End(memberlist(i)) & "," & comboname(0) & "," & maxP & "," & maxM2 & "," & maxM3 & "," & ratio(0)
            memberforce.WriteLine(line)
        Next
        memberforce.Close()

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
            Dim line As String = i & "," & Frequency(i - 1)
            modefrequency.WriteLine(line)
        Next i
        modefrequency.Close()

        Dim NumberNames As Integer
        Dim MyName() As String = {}
        SM.RespCombo.GetNameList(NumberNames, MyName)

        Dim F1() As Double = {}
        Dim F2() As Double = {}
        Dim F3() As Double = {}
        Dim M1() As Double = {}

        Dim nodeforce = New System.IO.StreamWriter(AppPath + "\SAP_O_NodeForce.txt", False)
        Dim nodeforce1 As String = "Node_ID,Member_ID,Section,Load_Combination,vertical_reaction_at_Column_Base,horizontal_reaction_x_at_Column_Base,horizontal_reaction_y_at_Column_Base"
        nodeforce.WriteLine(nodeforce1)
        Dim sec0 As String
        For i = 0 To nodelist.Count - 1

            If Node_memberID(nodelist(i)) <> "0" Then
                sec0 = Member_Size(Member_ID.IndexOf(Node_memberID(nodelist(i))))
            Else
                sec0 = "0"
            End If

            Dim line As String = Node_ID(nodelist(i)) & "," & Node_memberID(nodelist(i)) & "," & sec0

            For j = 0 To NumberNames - 1

                SM.Results.Setup.DeselectAllCasesAndCombosForOutput()
                SM.Results.Setup.SetComboSelectedForOutput(MyName(j))
                SM.Results.JointReact(Node_ID(nodelist(i)), 0, NumberResults, obj, elm, LoadCase, StepType, StepNum, F1, F2, F3, M1, M2, M3)

                If F1.Length <> 0 Then
                    line = line & "," & MyName(j) & "," & F3(0) & "," & F1(0) & "," & F2(0)
                End If

            Next
            nodeforce.WriteLine(line)
        Next
        nodeforce.Close()


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

            Next
            jointdispl.WriteLine(line)
        Next
        jointdispl.Close()


    End Sub
End Module
