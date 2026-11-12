import React, { useState } from 'react';
import { Faculty, Department, Group, User } from '../types';
import { 
  createFaculty, deleteFaculty, importFacultiesExcel, downloadFacultiesTemplate,
  createDepartment, deleteDepartment, importDepartmentsExcel, downloadDepartmentsTemplate, downloadDivisionsTemplate,
  createGroup, updateGroup, deleteGroup, assignTutorToGroup, importGroupsExcel, downloadGroupsTemplate
} from '../api';
import { 
  Landmark, Building, Users2, Plus, Trash2, 
  FileSpreadsheet, BookOpen, UserCheck, ShieldCheck, 
  Layers, Upload, CheckCircle2, Download, Pencil, X, RefreshCw 
} from 'lucide-react';

interface StructureProps {
  faculties: Faculty[];
  departments: Department[];
  groups: Group[];
  tutors: User[];
  onRefresh: () => void;
  isCompany?: boolean;
}

export const StructureView: React.FC<StructureProps> = ({ 
  faculties, 
  departments, 
  groups, 
  tutors, 
  onRefresh,
  isCompany
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'groups' | 'departments' | 'divisions' | 'faculties'>(isCompany ? 'divisions' : 'groups');
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (isCompany) {
      setActiveSubTab('divisions');
    }
  }, [isCompany]);

  // Modallar
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showDivisionModal, setShowDivisionModal] = useState(false);
  const [showFacultyModal, setShowFacultyModal] = useState(false);

  // Excel Modal
  const [excelModal, setExcelModal] = useState<{
    open: boolean;
    title: string;
    description: string;
    sampleHeader: string;
    templateName: string;
    templateFn?: () => void;
    onUpload: (file: File) => Promise<{ success: boolean; created: number; skipped: number }>;
  } | null>(null);

  // Form states
  const [groupName, setGroupName] = useState('');
  const [directionName, setDirectionName] = useState('');
  const [course, setCourse] = useState(1);
  const [selectedFacultyId, setSelectedFacultyId] = useState<number | undefined>(undefined);
  const [selectedDeptId, setSelectedDeptId] = useState<number | undefined>(undefined);
  const [selectedTutorId, setSelectedTutorId] = useState<number | undefined>(undefined);

  // Dept / Division form states
  const [deptName, setDeptName] = useState('');
  const [deptCode, setDeptCode] = useState('');
  const [deptFacultyId, setDeptFacultyId] = useState<number | undefined>(undefined);
  const [deptHeadId, setDeptHeadId] = useState<number | undefined>(undefined);

  // Faculty form
  const [facultyName, setFacultyName] = useState('');
  const [facultyCode, setFacultyCode] = useState('');

  // Filtrlangan kafedralar va bo'limlar
  const kafedralar = departments.filter(d => d.type === 'department');
  const bolimlar = departments.filter(d => d.type === 'division');

  // Tyutor biriktirish modal holati
  const [assignTutorModal, setAssignTutorModal] = useState<Group | null>(null);
  const [selectedModalTutorId, setSelectedModalTutorId] = useState<number | undefined>(undefined);
  const [assignLoading, setAssignLoading] = useState(false);

  const handleAssignTutor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignTutorModal) return;
    setAssignLoading(true);
    try {
      await assignTutorToGroup(assignTutorModal.id, selectedModalTutorId || null);
      setAssignTutorModal(null);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Tyutor biriktirishda xatolik yuz berdi");
    } finally {
      setAssignLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createGroup({
        name: groupName,
        direction_name: directionName,
        course: Number(course),
        faculty_id: selectedFacultyId ? Number(selectedFacultyId) : undefined,
        department_id: selectedDeptId ? Number(selectedDeptId) : undefined,
        tutor_id: selectedTutorId ? Number(selectedTutorId) : undefined
      });
      setShowGroupModal(false);
      setGroupName('');
      setDirectionName('');
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Guruh yaratishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createDepartment({
        name: deptName,
        code: deptCode || undefined,
        type: 'department',
        faculty_id: deptFacultyId ? Number(deptFacultyId) : undefined,
        head_id: deptHeadId ? Number(deptHeadId) : undefined,
        head_title: "Kafedra mudiri"
      });
      setShowDeptModal(false);
      setDeptName('');
      setDeptCode('');
      setDeptHeadId(undefined);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Kafedra yaratishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDivision = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createDepartment({
        name: deptName,
        code: deptCode || undefined,
        type: 'division',
        faculty_id: deptFacultyId ? Number(deptFacultyId) : undefined,
        head_id: deptHeadId ? Number(deptHeadId) : undefined,
        head_title: "Bo'lim boshlig'i"
      });
      setShowDivisionModal(false);
      setDeptName('');
      setDeptCode('');
      setDeptHeadId(undefined);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Bo'lim yaratishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createFaculty({
        name: facultyName,
        code: facultyCode || undefined
      });
      setShowFacultyModal(false);
      setFacultyName('');
      setFacultyCode('');
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Fakultet yaratishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  // Excel fayl yuklash bajaruvchisi
  const handleExcelUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!excelModal || !e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    setLoading(true);
    try {
      const res = await excelModal.onUpload(file);
      alert(`Muvaffaqiyatli yuklandi!\nQo'shildi: ${res.created} ta\nMavjud bo'lgani uchun o'tkazib yuborildi: ${res.skipped} ta`);
      setExcelModal(null);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Excel yuklashda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 bg-white border border-slate-200/80 p-5 sm:p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Landmark className="text-[#0084ff]" size={24} />
            {isCompany ? "Tashkiliy Tuzilma va Bo'limlar" : "Akademik va Tashkiliy Tuzilma"}
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            {isCompany 
              ? "Korxona bo'limlari, boshqarmalar va ularning mas'ul rahbarlari"
              : "Fakultetlar, Kafedralar, Bo'limlar, Talabalar guruhlari va ularga rahbarlar (Mudir, Boshliq, Tyutor) biriktirish"}
          </p>
        </div>

        {/* Sub-tab Switcher */}
        {isCompany ? (
          <div className="flex flex-wrap bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveSubTab('divisions')}
              className="px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 bg-[#0084ff] text-white shadow-sm"
            >
              <Layers size={15} /> Bo'limlar & Boshqarmalar ({bolimlar.length})
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveSubTab('groups')}
              className={`px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
                activeSubTab === 'groups' ? 'bg-[#0084ff] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users2 size={15} /> Guruhlar & Tyutorlar ({groups.length})
            </button>
            <button
              onClick={() => setActiveSubTab('departments')}
              className={`px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
                activeSubTab === 'departments' ? 'bg-[#0084ff] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Building size={15} /> Kafedralar ({kafedralar.length})
            </button>
            <button
              onClick={() => setActiveSubTab('divisions')}
              className={`px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
                activeSubTab === 'divisions' ? 'bg-[#0084ff] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers size={15} /> Bo'limlar ({bolimlar.length})
            </button>
            <button
              onClick={() => setActiveSubTab('faculties')}
              className={`px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
                activeSubTab === 'faculties' ? 'bg-[#0084ff] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Landmark size={15} /> Fakultetlar ({faculties.length})
            </button>
          </div>
        )}
      </div>

      {/* ========================================= */}
      {/* 1. GURUHLAR VA TYUTORLAR RO'YXATI         */}
      {/* ========================================= */}
      {activeSubTab === 'groups' && (
        <div className="space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <BookOpen className="text-[#0084ff]" size={18} />
              Guruhlar, Ta'lim Yo'nalishi va Guruh Rahbari (Tyutor)
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={downloadGroupsTemplate}
                title="Guruhlar namunaviy Excel shablonini yuklab olish"
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-semibold text-xs transition whitespace-nowrap"
              >
                <Download size={15} /> Shablon (.xlsx)
              </button>
              <button
                onClick={() => setExcelModal({
                  open: true,
                  title: "Guruhlarni massiv qo'shish",
                  description: "Excel faylda guruh nomi, ta'lim yo'nalishi, kursi va kafedra nomi bo'lishi kerak.",
                  sampleHeader: "Guruh_Nomi | Ta'lim_Yo'nalishi | Kurs | Kafedra_Nomi",
                  templateName: "guruhlar_shablon.xlsx",
                  templateFn: downloadGroupsTemplate,
                  onUpload: importGroupsExcel
                })}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 font-semibold text-xs transition whitespace-nowrap"
              >
                <FileSpreadsheet size={15} /> Massiv Qo'shish
              </button>
              <button
                onClick={() => setShowGroupModal(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-xs shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                <Plus size={16} /> Yangi Guruh
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="py-4 px-6">Guruh Nomi</th>
                    <th className="py-4 px-6">Ta'lim Yo'nalishi</th>
                    <th className="py-4 px-6">Kurs</th>
                    <th className="py-4 px-6">Kafedra / Fakultet</th>
                    <th className="py-4 px-6">Tyutor (Guruh Rahbari)</th>
                    <th className="py-4 px-6 text-center">Talabalar</th>
                    <th className="py-4 px-6 text-right">Amal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-sans">
                  {groups.map((g) => (
                    <tr key={g.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-4 px-6 font-mono font-bold text-base text-slate-900">
                        {g.name}
                      </td>
                      <td className="py-4 px-6 font-semibold text-[#0084ff]">
                        {g.direction_name || "Yo'nalish ko'rsatilmagan"}
                      </td>
                      <td className="py-4 px-6 font-semibold">
                        <span className="px-2.5 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700 border border-slate-200">
                          {g.course}-kurs
                        </span>
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-600">
                        <div className="font-semibold text-slate-800">{g.department_name || "-"}</div>
                        <div className="text-slate-400">{g.faculty_name || ""}</div>
                      </td>
                      <td className="py-4 px-6">
                        {g.tutor_name ? (
                          <button
                            type="button"
                            onClick={() => { setAssignTutorModal(g); setSelectedModalTutorId(g.tutor_id); }}
                            className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-slate-100 transition group text-left cursor-pointer border border-transparent hover:border-slate-200"
                            title="Tyutorni o'zgartirish uchun bosing"
                          >
                            <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center text-xs shrink-0">
                              {g.tutor_name[0]}
                            </div>
                            <div className="leading-tight">
                              <div className="font-bold text-xs text-slate-900 group-hover:text-[#0084ff] transition flex items-center gap-1.5">
                                <span>{g.tutor_name}</span>
                                <Pencil size={11} className="opacity-0 group-hover:opacity-100 text-[#0084ff]" />
                              </div>
                              <div className="text-[10px] text-slate-400">Tyutorni o'zgartirish</div>
                            </div>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => { setAssignTutorModal(g); setSelectedModalTutorId(undefined); }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 text-xs font-bold transition shadow-xs cursor-pointer"
                            title="Guruhga tyutor biriktirish"
                          >
                            <UserCheck size={14} />
                            <span>Tyutor biriktirish</span>
                          </button>
                        )}
                      </td>
                      <td className="py-4 px-6 text-center font-mono font-bold text-xs text-slate-700">
                        {g.student_count || 0} ta
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => { setAssignTutorModal(g); setSelectedModalTutorId(g.tutor_id); }}
                            className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 transition"
                            title="Tyutor biriktirish / o'zgartirish"
                          >
                            <UserCheck size={15} />
                          </button>
                          <button
                            onClick={async () => {
                              if (confirm("Guruhni o'chirmoqchimisiz?")) {
                                await deleteGroup(g.id);
                                onRefresh();
                              }
                            }}
                            className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 transition"
                            title="Guruhni o'chirish"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}

                  {groups.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-slate-400">
                        Hozircha guruhlar qo'shilmagan
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================= */}
      {/* 2. KAFEDRALAR (Kafedra mudiri bilan)       */}
      {/* ========================================= */}
      {activeSubTab === 'departments' && (
        <div className="space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <Building className="text-[#0084ff]" size={18} />
              Universitet Kafedralari va Kafedra Mudirlari
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={downloadDepartmentsTemplate}
                title="Kafedralar namunaviy Excel shablonini yuklab olish"
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-semibold text-xs transition whitespace-nowrap"
              >
                <Download size={15} /> Shablon (.xlsx)
              </button>
              <button
                onClick={() => setExcelModal({
                  open: true,
                  title: "Kafedralarni massiv qo'shish",
                  description: "Excel faylda kafedra nomi, kodi va fakultet nomi bo'lishi kerak.",
                  sampleHeader: "Kafedra_Nomi | Kodi | Fakultet_Nomi",
                  templateName: "kafedralar_shablon.xlsx",
                  templateFn: downloadDepartmentsTemplate,
                  onUpload: (f) => importDepartmentsExcel(f, 'department')
                })}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 font-semibold text-xs transition whitespace-nowrap"
              >
                <FileSpreadsheet size={15} /> Massiv Qo'shish
              </button>
              <button
                onClick={() => {
                  setDeptName('');
                  setDeptCode('');
                  setDeptHeadId(undefined);
                  setShowDeptModal(true);
                }}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-xs shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                <Plus size={16} /> Yangi Kafedra
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {kafedralar.map((d) => (
              <div key={d.id} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-mono font-bold text-[#0084ff] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {d.code || "KAFEDRA"}
                    </span>
                    <button
                      onClick={async () => {
                        if (confirm("Kafedrani o'chirishga ishonchingiz komilmi?")) {
                          await deleteDepartment(d.id);
                          onRefresh();
                        }
                      }}
                      className="text-slate-400 hover:text-rose-600 transition"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <h3 className="font-bold text-base text-slate-900 mt-2">{d.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Fakultet: <span className="font-medium text-slate-700">{d.faculty_name || "Umumiy"}</span>
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Kafedra Mudiri:</span>
                  {d.head_name ? (
                    <span className="font-bold text-slate-900 bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">
                      {d.head_name}
                    </span>
                  ) : (
                    <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      Mudir tayinlanmagan
                    </span>
                  )}
                </div>
              </div>
            ))}

            {kafedralar.length === 0 && (
              <div className="col-span-full py-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-300">
                Kafedralar mavjud emas
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================= */}
      {/* 3. BO'LIMLAR (Bo'lim boshlig'i bilan)       */}
      {/* ========================================= */}
      {activeSubTab === 'divisions' && (
        <div className="space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <Layers className="text-[#0084ff]" size={18} />
              Universitet Ma'muriy Bo'limlari va Bo'lim Boshliqlari
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={downloadDivisionsTemplate}
                title="Bo'limlar namunaviy Excel shablonini yuklab olish"
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-semibold text-xs transition whitespace-nowrap"
              >
                <Download size={15} /> Shablon (.xlsx)
              </button>
              <button
                onClick={() => setExcelModal({
                  open: true,
                  title: "Bo'limlarni massiv qo'shish",
                  description: "Excel faylda bo'lim nomi va bo'lim boshlig'i (F.I.SH) kiritiladi.",
                  sampleHeader: "Bo'lim Nomi | Bo'lim Boshlig'i (F.I.SH)",
                  templateName: "bolimlar_shablon.xlsx",
                  templateFn: downloadDivisionsTemplate,
                  onUpload: (f) => importDepartmentsExcel(f, 'division')
                })}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 font-semibold text-xs transition whitespace-nowrap"
              >
                <FileSpreadsheet size={15} /> Massiv Qo'shish
              </button>
              <button
                onClick={() => {
                  setDeptName('');
                  setDeptCode('');
                  setDeptHeadId(undefined);
                  setShowDivisionModal(true);
                }}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-xs shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                <Plus size={16} /> Yangi Bo'lim
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {bolimlar.map((b) => (
              <div key={b.id} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      {b.code || "BO'LIM"}
                    </span>
                    <button
                      onClick={async () => {
                        if (confirm("Bo'limni o'chirishga ishonchingiz komilmi?")) {
                          await deleteDepartment(b.id);
                          onRefresh();
                        }
                      }}
                      className="text-slate-400 hover:text-rose-600 transition"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <h3 className="font-bold text-base text-slate-900 mt-2">{b.name}</h3>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Bo'lim Boshlig'i:</span>
                  {b.head_name ? (
                    <span className="font-bold text-slate-900 bg-purple-50 text-purple-700 px-2 py-0.5 rounded border border-purple-200">
                      {b.head_name}
                    </span>
                  ) : (
                    <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      Boshliq tayinlanmagan
                    </span>
                  )}
                </div>
              </div>
            ))}

            {bolimlar.length === 0 && (
              <div className="col-span-full py-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-300">
                Hozircha bo'limlar kiritilmagan (Masalan: Rektorat, O'quv-uslubiy bo'lim, Kadrlar bo'limi)
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================= */}
      {/* 4. FAKULTETLAR RO'YXATI                   */}
      {/* ========================================= */}
      {activeSubTab === 'faculties' && (
        <div className="space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <Landmark className="text-[#0084ff]" size={18} />
              Universitet Fakultetlari
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={downloadFacultiesTemplate}
                title="Fakultetlar namunaviy Excel shablonini yuklab olish"
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-semibold text-xs transition whitespace-nowrap"
              >
                <Download size={15} /> Shablon (.xlsx)
              </button>
              <button
                onClick={() => setExcelModal({
                  open: true,
                  title: "Fakultetlarni massiv qo'shish",
                  description: "Excel faylda fakultet nomi va qisqa kodi bo'lishi kerak.",
                  sampleHeader: "Fakultet_Nomi | Kodi (Masalan: ATF)",
                  templateName: "fakultetlar_shablon.xlsx",
                  templateFn: downloadFacultiesTemplate,
                  onUpload: importFacultiesExcel
                })}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 font-semibold text-xs transition whitespace-nowrap"
              >
                <FileSpreadsheet size={15} /> Massiv Qo'shish
              </button>
              <button
                onClick={() => setShowFacultyModal(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-xs shadow-md shadow-[#0084ff]/20 transition whitespace-nowrap"
              >
                <Plus size={16} /> Yangi Fakultet
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {faculties.map((f) => (
              <div key={f.id} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      {f.code || "FAKULTET"}
                    </span>
                    <button
                      onClick={async () => {
                        if (confirm("Fakultetni o'chirmoqchimisiz?")) {
                          await deleteFaculty(f.id);
                          onRefresh();
                        }
                      }}
                      className="text-slate-400 hover:text-rose-600 transition"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <h3 className="font-bold text-base text-slate-900 mt-2">{f.name}</h3>
                </div>
              </div>
            ))}

            {faculties.length === 0 && (
              <div className="col-span-full py-12 text-center text-slate-400 bg-white rounded-2xl border border-dashed border-slate-300">
                Fakultetlar qo'shilmagan
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================= */}
      {/* MODAL: MASSIV EXCEL YUKLASH               */}
      {/* ========================================= */}
      {excelModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
              <FileSpreadsheet className="text-emerald-600" /> {excelModal.title}
            </h3>
            <p className="text-xs text-slate-500 mb-4">{excelModal.description}</p>

            {excelModal.templateFn && (
              <button 
                type="button"
                onClick={excelModal.templateFn}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-blue-50 hover:bg-blue-100 text-[#0084ff] border border-blue-200 font-bold text-xs transition mb-4 shadow-sm"
              >
                <Download size={16} /> Namunaviy Shablonni Yuklab Olish ({excelModal.templateName})
              </button>
            )}

            <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl mb-4 text-xs font-mono text-slate-700">
              <span className="text-slate-400 block mb-1 text-[11px] font-sans">Namuna ustunlari (1-qatorda):</span>
              <div className="font-bold text-emerald-800 break-words leading-relaxed text-[11px]">
                {excelModal.sampleHeader}
              </div>
            </div>

            <div className="border-2 border-dashed border-slate-300 rounded-2xl p-6 text-center hover:border-emerald-500 transition mb-4">
              <input 
                type="file" 
                accept=".xlsx,.xls"
                id="excel-file-input"
                onChange={handleExcelUpload}
                className="hidden" 
              />
              <label 
                htmlFor="excel-file-input"
                className="cursor-pointer flex flex-col items-center justify-center"
              >
                <Upload size={32} className="text-emerald-600 mb-2" />
                <span className="text-sm font-bold text-slate-800">Excel faylini tanlang (.xlsx)</span>
                <span className="text-xs text-slate-400 mt-1">Fayl tanlanganda avtomatik yuklanadi</span>
              </label>
            </div>

            <button
              onClick={() => setExcelModal(null)}
              className="w-full py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
            >
              Yopish
            </button>
          </div>
        </div>
      )}

      {/* ========================================= */}
      {/* MODAL: GURUH QO'SHISH                     */}
      {/* ========================================= */}
      {showGroupModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-lg rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Users2 className="text-[#0084ff]" /> Yangi Guruh, Ta'lim Yo'nalishi va Tyutor Biriktirish
            </h3>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Guruh Nomi (Masalan: 941-21)</label>
                  <input
                    type="text"
                    placeholder="941-21"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    required
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Kurs</label>
                  <select
                    value={course}
                    onChange={(e) => setCourse(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  >
                    <option value={1}>1-kurs</option>
                    <option value={2}>2-kurs</option>
                    <option value={3}>3-kurs</option>
                    <option value={4}>4-kurs</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Ta'lim Yo'nalishi</label>
                <input
                  type="text"
                  placeholder="Dasturiy injiniring (kunduzgi)"
                  value={directionName}
                  onChange={(e) => setDirectionName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Fakultet</label>
                  <select
                    value={selectedFacultyId || ''}
                    onChange={(e) => setSelectedFacultyId(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  >
                    <option value="">Fakultetni tanlang</option>
                    {faculties.map((f) => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Kafedra</label>
                  <select
                    value={selectedDeptId || ''}
                    onChange={(e) => setSelectedDeptId(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                  >
                    <option value="">Kafedrani tanlang</option>
                    {kafedralar.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Tyutor (Guruh Rahbari)</label>
                <select
                  value={selectedTutorId || ''}
                  onChange={(e) => setSelectedTutorId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                >
                  <option value="">Tyutorni biriktirish (Tanlang)</option>
                  {tutors.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} ({t.position || t.role})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowGroupModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Saqlanmoqda..." : "Guruhni Saqlash"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: KAFEDRA QO'SHISH (Mudir biriktirish bilan) */}
      {showDeptModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Building className="text-[#0084ff]" /> Yangi Kafedra va Mudir Biriktirish
            </h3>
            <form onSubmit={handleCreateDept} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Kafedra Nomi</label>
                <input
                  type="text"
                  placeholder="Dasturiy Muhandislik kafedrasi"
                  value={deptName}
                  onChange={(e) => setDeptName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Kodi (Qisqartmasi)</label>
                <input
                  type="text"
                  placeholder="DM"
                  value={deptCode}
                  onChange={(e) => setDeptCode(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Tegishli Fakultet</label>
                <select
                  value={deptFacultyId || ''}
                  onChange={(e) => setDeptFacultyId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                >
                  <option value="">Fakultetni tanlang</option>
                  {faculties.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Kafedra Mudiri</label>
                <select
                  value={deptHeadId || ''}
                  onChange={(e) => setDeptHeadId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                >
                  <option value="">Mudirni tanlang (Xodimlar orasidan)</option>
                  {tutors.map((t) => (
                    <option key={t.id} value={t.id}>{t.full_name} ({t.position || t.role})</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowDeptModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Saqlanmoqda..." : "Kafedrani Saqlash"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: BO'LIM QO'SHISH (Boshliq biriktirish bilan) */}
      {showDivisionModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Layers className="text-[#0084ff]" /> Yangi Ma'muriy Bo'lim va Boshliq Biriktirish
            </h3>
            <form onSubmit={handleCreateDivision} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Bo'lim Nomi</label>
                <input
                  type="text"
                  placeholder="Masalan: O'quv-uslubiy bo'lim, Kadrlar bo'limi"
                  value={deptName}
                  onChange={(e) => setDeptName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Kodi (Qisqartmasi)</label>
                <input
                  type="text"
                  placeholder="OUB"
                  value={deptCode}
                  onChange={(e) => setDeptCode(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Bo'lim Boshlig'i</label>
                <select
                  value={deptHeadId || ''}
                  onChange={(e) => setDeptHeadId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                >
                  <option value="">Bo'lim boshlig'ini tanlang</option>
                  {tutors.map((t) => (
                    <option key={t.id} value={t.id}>{t.full_name} ({t.position || t.role})</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowDivisionModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Saqlanmoqda..." : "Bo'limni Saqlash"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: FAKULTET QO'SHISH */}
      {showFacultyModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-2xl p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Landmark className="text-[#0084ff]" /> Yangi Fakultet Qo'shish
            </h3>
            <form onSubmit={handleCreateFaculty} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Fakultet Nomi</label>
                <input
                  type="text"
                  placeholder="Axborot Texnologiyalari Fakulteti"
                  value={facultyName}
                  onChange={(e) => setFacultyName(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Kodi (Qisqartmasi)</label>
                <input
                  type="text"
                  placeholder="ATF"
                  value={facultyCode}
                  onChange={(e) => setFacultyCode(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-slate-900 text-sm focus:outline-none focus:border-[#0084ff] focus:bg-white font-mono"
                />
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowFacultyModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-semibold text-sm transition shadow-md shadow-[#0084ff]/20"
                >
                  {loading ? "Saqlanmoqda..." : "Fakultetni Saqlash"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GURUHGA TYUTOR BIRIKTIRISH / O'ZGARTIRISH */}
      {assignTutorModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 w-full max-w-md rounded-3xl p-6 shadow-2xl relative font-sans animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-[#0084ff] border border-blue-100 flex items-center justify-center">
                  <UserCheck size={20} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Guruhga Tyutor Biriktirish</h3>
                  <p className="text-[11px] text-slate-400">Guruh: <strong className="text-slate-800 font-mono font-bold">{assignTutorModal.name}</strong> ({assignTutorModal.course}-kurs)</p>
                </div>
              </div>
              <button 
                onClick={() => setAssignTutorModal(null)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAssignTutor} className="space-y-4">
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5 space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Ta'lim Yo'nalishi:</span>
                  <span className="font-semibold text-slate-800">{assignTutorModal.direction_name || "Mavjud emas"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Kafedra:</span>
                  <span className="font-semibold text-slate-800">{assignTutorModal.department_name || "-"}</span>
                </div>
                <div className="flex justify-between items-center pt-1 border-t border-slate-200">
                  <span className="text-slate-500">Amaldagi Tyutor:</span>
                  <span className="font-bold text-emerald-700">
                    {assignTutorModal.tutor_name ? `✅ ${assignTutorModal.tutor_name}` : "Biriktirilmagan"}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Guruh Rahbari (Tyutor)ni tanlang <span className="text-rose-500">*</span>
                </label>
                <select
                  value={selectedModalTutorId || ''}
                  onChange={(e) => setSelectedModalTutorId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-[#0084ff] focus:bg-white transition"
                >
                  <option value="">Tyutor biriktirilmasin (Bo'shatish)</option>
                  {tutors.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} ({t.position || t.role} {t.department_name ? `- ${t.department_name}` : ''})
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Universitet xodimlari ro'yxatidan mas'ul tyutorni tanlang
                </p>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setAssignTutorModal(null)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-50 transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={assignLoading}
                  className="flex-1 py-2.5 rounded-xl bg-[#0084ff] hover:bg-[#0073e0] text-white font-bold text-xs transition shadow-md shadow-[#0084ff]/20 flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {assignLoading ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      <span>Saqlanmoqda...</span>
                    </>
                  ) : (
                    <span>Saqlash</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
