import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useToast } from "../components/shared/ToastContext.ts";
import { Card, CardContent, CardHeader } from "../components/shared/Card.tsx";
import { Button } from "../components/shared/Button.tsx";
import { Input } from "../components/shared/Input.tsx";
import { FormField } from "../components/shared/FormField.tsx";
import { Spinner } from "../components/shared/Spinner.tsx";
import {
  getYouTubeRecommendations,
  type YouTubeRecommendationsResponse,
  type YouTubeVideo,
} from "../services/youtube.ts";

export const YouTubeRecommendationsPage = () => {
  const { push } = useToast();

  const [skillsInput, setSkillsInput] = useState("");
  const [targetJob, setTargetJob] = useState("");
  const [timeframeMonths, setTimeframeMonths] = useState("6");
  const [recommendations, setRecommendations] =
    useState<YouTubeRecommendationsResponse | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!skillsInput.trim()) {
        throw new Error("Please enter your skills (comma-separated)");
      }

      if (!targetJob.trim()) {
        throw new Error("Please enter your target job role");
      }

      // Parse skills from comma-separated input
      const skillNames = skillsInput
        .split(",")
        .map((skill) => skill.trim())
        .filter((skill) => skill.length > 0);

      if (skillNames.length === 0) {
        throw new Error("Please enter at least one skill");
      }

      return getYouTubeRecommendations({
        current_skills: skillNames,
        target_job: targetJob,
        timeframe_months: parseInt(timeframeMonths),
        additional_context: {},
      });
    },
    onSuccess: (data) => {
      setRecommendations(data);
      push({
        title: "Recommendations loaded!",
        description: "YouTube videos and career timeline ready",
        tone: "success",
      });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Failed to load recommendations";
      push({
        title: "Error",
        description: message,
        tone: "error",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  if (!recommendations) {
    return (
      <div className="space-y-6">
        <div className="pb-6 border-b border-slate-800">
          <h1 className="text-4xl font-bold text-blue-400 mb-3">
            YouTube Learning Path
          </h1>
          <p className="text-slate-400 text-sm">
            Get personalized YouTube recommendations based on your career goal
          </p>
        </div>

        <Card>
          <CardHeader title="Learning Path Details" />
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <FormField label="Current Skills (comma-separated)">
                <Input
                  type="text"
                  placeholder="e.g., Python, SQL, JavaScript"
                  value={skillsInput}
                  onChange={(e) => setSkillsInput(e.target.value)}
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  Enter multiple skills separated by commas
                </p>
              </FormField>

              <FormField label="Target Job Role">
                <Input
                  type="text"
                  placeholder="e.g., Data Scientist, Full Stack Developer"
                  value={targetJob}
                  onChange={(e) => setTargetJob(e.target.value)}
                  required
                />
              </FormField>

              <FormField label="Timeframe (months)">
                <Input
                  type="number"
                  min="1"
                  max="24"
                  placeholder="e.g., 6"
                  value={timeframeMonths}
                  onChange={(e) => setTimeframeMonths(e.target.value)}
                  required
                />
              </FormField>

              <Button
                type="submit"
                disabled={mutation.isPending}
                className="w-full"
              >
                {mutation.isPending ? (
                  <>
                    <Spinner />
                    Loading recommendations...
                  </>
                ) : (
                  "Get Recommendations"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="pb-6 border-b border-slate-800">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-grow">
            <h1 className="text-4xl font-bold text-blue-400 mb-3">
              {recommendations.title}
            </h1>
            <p className="text-slate-400 text-sm max-w-3xl">
              {recommendations.summary}
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={() => {
              setRecommendations(null);
              setSkillsInput("");
              setTargetJob("");
              setTimeframeMonths("6");
            }}
            className="flex-shrink-0"
          >
            ← Back
          </Button>
        </div>
      </div>

      {/* YouTube Videos Section */}
      {recommendations.youtube_resources && recommendations.youtube_resources.length > 0 && (
        <Card>
          <CardHeader
            title="Recommended Learning Videos"
            description={`${recommendations.youtube_resources.length} curated videos to help you get started`}
          />
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.youtube_resources.map((video: YouTubeVideo, idx: number) => (
                <a
                  key={idx}
                  href={video.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex flex-col h-full p-4 bg-gradient-to-br from-slate-900/50 to-slate-800/50 hover:from-slate-900 hover:to-slate-800 rounded-xl border border-slate-700 hover:border-blue-500 transition-all duration-300 group overflow-hidden"
                >
                  {/* Video Thumbnail Area */}
                  <div className="relative mb-4 bg-slate-950 rounded-lg overflow-hidden h-32 flex items-center justify-center">
                    <svg
                      className="w-12 h-12 text-blue-400/30 group-hover:text-blue-400/50 transition"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                    </svg>
                  </div>

                  {/* Video Info */}
                  <div className="flex-grow flex flex-col">
                    <h3 className="font-bold text-white group-hover:text-blue-300 transition line-clamp-2 text-sm mb-2">
                      {video.title}
                    </h3>
                    <p className="text-xs text-slate-400 mb-3">{video.channel}</p>

                    {/* Metadata */}
                    <div className="space-y-2 text-xs text-slate-500 mt-auto">
                      {video.views && (
                        <div className="flex items-center gap-2 flex-wrap">
                          <svg
                            className="w-3 h-3 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                          <span>
                            {typeof video.views === 'string' 
                              ? video.views 
                              : parseInt(video.views).toLocaleString()} views
                          </span>
                        </div>
                      )}
                      {video.duration && (
                        <div className="flex items-center gap-2">
                          <svg
                            className="w-3 h-3 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <span>{video.duration}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* External Link Icon */}
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-blue-400 group-hover:text-blue-300">Watch on YouTube</span>
                      <svg
                        className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Learning Tips Section */}
      {recommendations.tips && recommendations.tips.length > 0 && (
        <Card>
          <CardHeader
            title="Learning Tips"
            description="Best practices to accelerate your learning"
          />
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {recommendations.tips.map((tip: string, idx: number) => (
                <div key={idx} className="flex gap-3 p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                  <svg
                    className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <p className="text-sm text-slate-300">{tip}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
