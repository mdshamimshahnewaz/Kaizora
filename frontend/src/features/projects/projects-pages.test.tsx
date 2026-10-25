import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, Link } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import { accessApi } from "@/features/identity/access-api";
import { organizationsApi } from "@/features/organizations/api";
import { projectsApi, type Project } from "./api";
import { ProjectsPage, ProjectDetailPage } from "./projects-pages";
vi.mock("./api",()=>({projectsApi:{list:vi.fn(),get:vi.fn(),create:vi.fn(),update:vi.fn(),transition:vi.fn(),access:vi.fn(),grant:vi.fn(),end:vi.fn(),options:vi.fn()}}));
vi.mock("@/features/identity/access-api",()=>({accessApi:{permissions:vi.fn()}}));
vi.mock("@/features/organizations/api",()=>({organizationsApi:{get:vi.fn()}}));
const project:Project={id:"p1",name:"Build",code:"BUILD",type:"delivery",status:"draft",client_id:null,client_name:"",description:"",start_date:null,target_end_date:null,version:1,created_at:"2026-10-18T00:00:00Z",capabilities:["projects.read","projects.manage","projects.transition","projects.access.read","projects.access.manage"]};
function open(detail=false){return render(<MemoryRouter initialEntries={[`/app/o/a/projects${detail?"/p1":""}`]}><Link to="/app/o/b/projects">Switch scope</Link><Routes><Route path="/app/o/:orgId/projects" element={<ProjectsPage/>}/><Route path="/app/o/:orgId/projects/:projectId" element={<ProjectDetailPage/>}/></Routes></MemoryRouter>);}
beforeEach(()=>{
  vi.resetAllMocks();Element.prototype.scrollIntoView=vi.fn();Element.prototype.hasPointerCapture=vi.fn(()=>false);Element.prototype.releasePointerCapture=vi.fn();
  vi.mocked(accessApi.permissions).mockResolvedValue({organization_id:"a",membership_id:"m1",is_owner:false,permissions:["projects.create"]});
  vi.mocked(organizationsApi.get).mockResolvedValue({id:"a",name:"Org",timezone:"Asia/Dhaka",status:"active",version:1,membership_id:"m1",is_owner:false});
  vi.mocked(projectsApi.list).mockResolvedValue({count:1,results:[project],next:null,previous:null});
  vi.mocked(projectsApi.get).mockResolvedValue(project);
  vi.mocked(projectsApi.access).mockResolvedValue({count:0,results:[],next:null,previous:null});
  vi.mocked(projectsApi.options).mockImplementation(async(_org,kind)=>({count:1,results:[{id:kind==="members"?"m1":"r1",label:kind==="members"?"Jane Manager":"Project manager"}],next:null,previous:null}));
});
it("creates with readable explicit manager and role choices",async()=>{
  const user=userEvent.setup();vi.mocked(projectsApi.create).mockResolvedValue(project);open();
  await user.click(await screen.findByRole("button",{name:"Create project"}));const form=within(screen.getByRole("dialog"));
  await user.type(form.getByLabelText("Project code"),"BUILD");await user.type(form.getByLabelText("Project name"),"Build");
  await user.click(form.getByRole("button",{name:"Choose initial manager"}));await user.click(await screen.findByRole("option",{name:"Jane Manager"}));
  await user.click(form.getByRole("button",{name:"Choose manager role"}));await user.click(await form.findByRole("button",{name:"Project manager"}));
  await user.click(form.getByRole("button",{name:"Create project"}));
  expect(projectsApi.create).toHaveBeenCalledWith("a",expect.objectContaining({code:"BUILD",initial_manager_membership_id:"m1",initial_manager_role_id:"r1",client_id:null}));expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
it("retains a draft after refresh failure and requires explicit conflict review",async()=>{
  const user=userEvent.setup();vi.mocked(projectsApi.update).mockRejectedValueOnce(Object.assign(new Error("Changed"),{status:409})).mockResolvedValue({...project,version:3});open(true);
  await user.click(await screen.findByRole("button",{name:"Edit project"}));const form=within(screen.getByRole("dialog"));await user.clear(form.getByLabelText("Project name"));await user.type(form.getByLabelText("Project name"),"My draft");await user.type(form.getByLabelText("Reason for change"),"Rename");
  vi.mocked(projectsApi.get).mockRejectedValueOnce(new TypeError("Offline"));await act(async()=>window.dispatchEvent(new Event("focus")));expect(form.getByLabelText("Project name")).toHaveValue("My draft");
  await user.click(form.getByRole("button",{name:"Save project"}));expect(await form.findByText("Changed")).toBeInTheDocument();expect(form.getByRole("button",{name:"Save project"})).toBeDisabled();
  vi.mocked(projectsApi.get).mockResolvedValue({...project,name:"Latest",version:2});await user.click(form.getByRole("button",{name:"Review latest version"}));expect(await form.findByText(/Latest: Latest/)).toBeInTheDocument();await user.click(form.getByRole("button",{name:"Save project"}));expect(projectsApi.update).toHaveBeenLastCalledWith("a","p1",expect.objectContaining({name:"My draft",version:2}));
});
it("removes stale open editor after permission revocation",async()=>{
  const user=userEvent.setup();open(true);await user.click(await screen.findByRole("button",{name:"Edit project"}));
  vi.mocked(projectsApi.get).mockRejectedValue(Object.assign(new Error("Project not found"),{status:404}));await act(async()=>window.dispatchEvent(new Event("focus")));
  expect(await screen.findByText("Project not found")).toBeInTheDocument();expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
it("hides mutations for a read-only project grant",async()=>{
  vi.mocked(projectsApi.get).mockResolvedValue({...project,capabilities:["projects.read"]});open(true);expect(await screen.findByRole("heading",{name:"Build"})).toBeInTheDocument();expect(screen.queryByRole("button",{name:"Edit project"})).not.toBeInTheDocument();expect(projectsApi.access).not.toHaveBeenCalled();
});
it("drops late project list responses after organization switch",async()=>{
  let resolve!:(value:Awaited<ReturnType<typeof projectsApi.list>>)=>void;
  vi.mocked(projectsApi.list).mockImplementationOnce(()=>new Promise(done=>{resolve=done;})).mockResolvedValue({count:0,results:[],next:null,previous:null});const user=userEvent.setup();open();await user.click(screen.getByRole("link",{name:"Switch scope"}));await screen.findByText(/No visible projects/);
  await act(async()=>resolve({count:1,results:[project],next:null,previous:null}));expect(screen.queryByRole("link",{name:"Build"})).not.toBeInTheDocument();
});
it("archives with reason and retains lifecycle intent",async()=>{
  const user=userEvent.setup();vi.mocked(projectsApi.transition).mockResolvedValue({...project,status:"archived",version:2});open(true);await user.click(await screen.findByRole("button",{name:"Move to archived"}));const form=within(screen.getByRole("dialog"));expect(form.getByText(/Archiving stops ordinary edits/)).toBeInTheDocument();await user.type(form.getByLabelText("Reason for change"),"Finished");await user.click(form.getByRole("button",{name:"Move to archived"}));expect(projectsApi.transition).toHaveBeenCalledWith("a","p1",{target_status:"archived",version:1,reason:"Finished"});
});
it("ends a selected grant with its version and explicit reason",async()=>{
  const grant={id:"g1",membership_id:"m1",member_name:"Jane",role_id:"r1",role_name:"Reader",started_at:"2026-10-18T00:00:00Z",ended_at:null,version:2};
  vi.mocked(projectsApi.access).mockResolvedValue({count:1,results:[grant],next:null,previous:null});vi.mocked(projectsApi.end).mockResolvedValue({...grant,version:3,ended_at:"2026-10-18T01:00:00Z"});
  const user=userEvent.setup();open(true);await user.click(await screen.findByRole("button",{name:"End access"}));const form=within(screen.getByRole("dialog"));expect(form.getByText(/Historical attribution is preserved/)).toBeInTheDocument();await user.type(form.getByLabelText("Reason for ending access"),"Assignment finished");await user.click(form.getByRole("button",{name:"End access"}));expect(projectsApi.end).toHaveBeenCalledWith("a","p1","g1",{version:2,reason:"Assignment finished"});
});
