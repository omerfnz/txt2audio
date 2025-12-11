import { FileUpload } from '../components/FileUpload';
import { createProject, startProcessing } from '../api/client';

interface UploadViewProps {
    onProjectCreated: (projectId: number) => void;
}

export const UploadView = ({ onProjectCreated }: UploadViewProps) => {
    const handleUpload = async (data: {
        text: File;
        audio: File | null;
        referenceVoicePath: string | null;
        useGpu: boolean;
        name: string;
        presetId: string;
        language: string;
        speed: number;
        temperature: number;
        topK: number;
        topP: number;
        repetitionPenalty: number;
    }) => {
        try {
            const formData = new FormData();
            formData.append('name', data.name);
            formData.append('text_file', data.text);
            formData.append('use_gpu', String(data.useGpu));
            formData.append('preset_id', data.presetId);
            formData.append('language', data.language);
            formData.append('speed', String(data.speed));
            formData.append('temperature', String(data.temperature));
            formData.append('top_k', String(data.topK));
            formData.append('top_p', String(data.topP));
            formData.append('repetition_penalty', String(data.repetitionPenalty));

            if (data.audio) {
                formData.append('voice_file', data.audio);
            } else if (data.referenceVoicePath) {
                formData.append('reference_voice_path', data.referenceVoicePath);
            }

            const res = await createProject(formData);

            // Start processing immediately
            await startProcessing(res.project_id, data.useGpu);

            onProjectCreated(res.project_id);
        } catch (error) {
            console.error(error);
            alert(`Error creating project: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    };

    return (
        <div className="h-full overflow-y-auto">
            <div className="min-h-full flex items-center justify-center p-6">
                <FileUpload onUpload={handleUpload} />
            </div>
        </div>
    );
};
