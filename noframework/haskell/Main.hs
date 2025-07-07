{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE RecordWildCards #-}

module Main where

import Control.Monad (when, unless)
import Control.Exception (catch, SomeException)
import Data.Aeson
import Data.Aeson.Encode.Pretty (encodePretty)
import qualified Data.ByteString.Lazy as BL
import qualified Data.ByteString.Lazy.Char8 as BL8
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import qualified Data.Text.Encoding as TE
import Data.Time
import GHC.Generics
import Network.HTTP.Simple
import System.Directory
import System.Environment
import System.Exit
import System.FilePath
import System.IO
import System.Process
import Text.Regex.TDFA

-- Data types
data Args = Args
    { repo :: String
    , promptFile :: String
    , outputDir :: String
    , fileName :: Maybe String
    , model :: String
    } deriving (Show)

data ChatMessage = ChatMessage
    { role :: T.Text
    , content :: T.Text
    } deriving (Generic)

instance ToJSON ChatMessage
instance FromJSON ChatMessage

data ChatRequest = ChatRequest
    { chatModel :: T.Text
    , messages :: [ChatMessage]
    , temperature :: Double
    , max_tokens :: Int
    } deriving (Generic)

instance ToJSON ChatRequest where
    toJSON ChatRequest{..} = object
        [ "model" .= chatModel
        , "messages" .= messages
        , "temperature" .= temperature
        , "max_tokens" .= max_tokens
        ]

data ChatChoice = ChatChoice
    { message :: ChatMessage
    } deriving (Generic)

instance FromJSON ChatChoice

data ChatResponse = ChatResponse
    { choices :: [ChatChoice]
    } deriving (Generic)

instance FromJSON ChatResponse

data Metadata = Metadata
    { metaRepo :: T.Text
    , metaPromptFile :: T.Text
    , metaModel :: T.Text
    , metaTimestamp :: T.Text
    , wordCount :: Int
    , charCount :: Int
    } deriving (Generic)

instance ToJSON Metadata where
    toJSON Metadata{..} = object
        [ "repository" .= metaRepo
        , "prompt_file" .= metaPromptFile
        , "model" .= metaModel
        , "timestamp" .= metaTimestamp
        , "word_count" .= wordCount
        , "char_count" .= charCount
        ]

-- Main entry point
main :: IO ()
main = do
    args <- getArgs
    case parseArgs args defaultArgs of
        Left err -> do
            hPutStrLn stderr $ "Error: " ++ err
            printUsage
            exitFailure
        Right parsedArgs -> runTechWriter parsedArgs

-- Default arguments
defaultArgs :: Args
defaultArgs = Args
    { repo = ""
    , promptFile = ""
    , outputDir = "output"
    , fileName = Nothing
    , model = "openai/gpt-4o-mini"
    }

-- Parse command line arguments
parseArgs :: [String] -> Args -> Either String Args
parseArgs [] args
    | null (repo args) = Left "Missing required argument: --repo"
    | null (promptFile args) = Left "Missing required argument: --prompt"
    | otherwise = Right args
parseArgs ("--repo":r:rest) args = parseArgs rest args { repo = r }
parseArgs ("--prompt":p:rest) args = parseArgs rest args { promptFile = p }
parseArgs ("--output-dir":d:rest) args = parseArgs rest args { outputDir = d }
parseArgs ("--file-name":f:rest) args = parseArgs rest args { fileName = Just f }
parseArgs ("--model":m:rest) args = parseArgs rest args { model = m }
parseArgs (unknown:_) _ = Left $ "Unknown argument: " ++ unknown

-- Print usage
printUsage :: IO ()
printUsage = putStrLn $ unlines
    [ "Usage: tech-writer.sh [OPTIONS]"
    , ""
    , "Required options:"
    , "  --repo URL          GitHub repository URL"
    , "  --prompt FILE       Path to prompt file"
    , ""
    , "Optional options:"
    , "  --output-dir DIR    Output directory (default: output)"
    , "  --file-name NAME    Output file name"
    , "  --model MODEL       LLM model to use (default: openai/gpt-4o-mini)"
    ]

-- Run the tech writer
runTechWriter :: Args -> IO ()
runTechWriter args@Args{..} = do
    -- Set up logging
    logDir <- createLogDir
    logFile <- createLogFile logDir
    
    logInfo logFile "Starting Tech Writer Agent"
    logInfo logFile $ "Model: " ++ model
    
    -- Read prompt
    promptContent <- TIO.readFile promptFile
    
    -- Clone or update repository
    repoPath <- cloneOrUpdateRepo repo logFile
    logInfo logFile $ "Repository path: " ++ repoPath
    
    -- Run ReAct agent
    logInfo logFile "Starting ReAct agent"
    result <- reactLoop repoPath (T.unpack promptContent) model 1 15 [] logFile
    
    -- Save results
    createDirectoryIfMissing True outputDir
    outputFile <- case fileName of
        Just f -> return $ outputDir </> f
        Nothing -> do
            timestamp <- formatTime defaultTimeLocale "%Y%m%d-%H%M%S" <$> getCurrentTime
            return $ outputDir </> ("tech-writer-" ++ timestamp ++ ".md")
    
    writeFile outputFile result
    logInfo logFile $ "Results saved to: " ++ outputFile
    
    -- Save metadata
    let metadataFile = replaceExtension outputFile ".metadata.json"
    saveMetadata args result outputFile metadataFile
    logInfo logFile $ "Metadata saved to: " ++ metadataFile

-- Create log directory
createLogDir :: IO FilePath
createLogDir = do
    let logDir = "logs"
    createDirectoryIfMissing True logDir
    return logDir

-- Create log file
createLogFile :: FilePath -> IO FilePath
createLogFile logDir = do
    timestamp <- formatTime defaultTimeLocale "%Y%m%d-%H%M%S" <$> getCurrentTime
    let logFile = logDir </> ("tech-writer-" ++ timestamp ++ ".log")
    return logFile

-- Logging functions
logInfo :: FilePath -> String -> IO ()
logInfo = logMessage "INFO"

logDebug :: FilePath -> String -> IO ()
logDebug = logMessage "DEBUG"

logMessage :: String -> FilePath -> String -> IO ()
logMessage level logFile msg = do
    timestamp <- formatTime defaultTimeLocale "%Y-%m-%d %H:%M:%S" <$> getCurrentTime
    let logLine = timestamp ++ " - " ++ level ++ " - " ++ msg
    putStrLn logLine
    appendFile logFile (logLine ++ "\n")

-- Clone or update repository
cloneOrUpdateRepo :: String -> FilePath -> IO String
cloneOrUpdateRepo repoUrl logFile = do
    home <- getHomeDirectory
    let repoName = takeFileName $ dropTrailingPathSeparator repoUrl
        -- Extract organization/repo from URL
        repoPath = case reverse $ splitDirectories repoUrl of
            (repo:org:_) -> home </> ".cache" </> "github" </> org </> repo
            _ -> home </> ".cache" </> "github" </> repoName
    
    createDirectoryIfMissing True (takeDirectory repoPath)
    
    exists <- doesDirectoryExist (repoPath </> ".git")
    if exists
        then do
            logInfo logFile $ "Updating existing repository: " ++ repoPath
            callProcess "git" ["-C", repoPath, "pull", "--quiet"]
        else do
            logInfo logFile $ "Cloning repository: " ++ repoUrl
            callProcess "git" ["clone", "--quiet", repoUrl, repoPath]
    
    return repoPath

-- ReAct agent loop
reactLoop :: String -> String -> String -> Int -> Int -> [(String, String)] -> FilePath -> IO String
reactLoop repoPath prompt model step maxSteps memory logFile
    | step > maxSteps = return $ extractFinalAnswer memory
    | otherwise = do
        logInfo logFile $ "Step " ++ show step ++ "/" ++ show maxSteps
        
        -- Prepare prompt for LLM
        let systemPrompt = getSystemPrompt
            userPrompt = buildUserPrompt repoPath prompt memory
        
        -- Call LLM
        response <- callLLM model systemPrompt userPrompt logFile
        
        -- Parse response
        case parseLLMResponse response of
            FinalAnswer answer -> do
                logInfo logFile "Final answer received"
                return answer
            Action action actionInput -> do
                logInfo logFile $ "Executing action: " ++ action ++ " with input: " ++ actionInput
                -- Execute action
                observation <- executeAction action actionInput repoPath logFile
                logInfo logFile $ "Action result: " ++ take 100 observation ++ if length observation > 100 then "..." else ""
                
                -- Add to memory
                let thought = extractThought response
                    newMemory = memory ++ 
                        [ ("thought", thought)
                        , ("action", action)
                        , ("action_input", actionInput)
                        , ("observation", observation)
                        ]
                
                -- Continue loop
                reactLoop repoPath prompt model (step + 1) maxSteps newMemory logFile
            NoAction -> do
                logInfo logFile "No valid action found in response"
                reactLoop repoPath prompt model (step + 1) maxSteps memory logFile

-- Get system prompt
getSystemPrompt :: String
getSystemPrompt = unlines
    [ "You are a technical documentation assistant that analyses codebases and generates comprehensive documentation."
    , ""
    , "When given a directory path and a specific analysis request, you will:"
    , "1. Explore the codebase structure to understand its organization"
    , "2. Read relevant files to comprehend the implementation details"
    , "3. Generate detailed technical documentation based on your analysis"
    , ""
    , "You have access to tools that help you explore and understand codebases:"
    , "- find_all_matching_files: Find files matching patterns in directories"
    , "- read_file: Read the contents of specific files"
    , ""
    , "Important guidelines:"
    , "- Always start by exploring the directory structure to understand the codebase layout"
    , "- Read files strategically based on the documentation needs"
    , "- Pay attention to configuration files, main entry points, and key modules"
    , "- Generate clear, well-structured documentation that would help developers understand the codebase"
    , ""
    , "Use the following format:"
    , ""
    , "Thought: I need to [describe what you need to do next]"
    , "Action: [tool_name]"
    , "Action Input: {\"param\": \"value\"}"
    , "Observation: [tool output will be provided here]"
    , ""
    , "... (repeat Thought/Action/Observation as needed)"
    , ""
    , "Thought: I have gathered enough information to provide the final answer"
    , "Final Answer: [Your comprehensive documentation/analysis]"
    ]

-- Build user prompt
buildUserPrompt :: String -> String -> [(String, String)] -> String
buildUserPrompt repoPath prompt memory =
    "Analyze the codebase at: " ++ repoPath ++ "\n\n" ++
    "Request: " ++ prompt ++ "\n\n" ++
    formatMemory memory

-- Format memory for prompt
formatMemory :: [(String, String)] -> String
formatMemory [] = ""
formatMemory memory = unlines $ map formatItem memory
  where
    formatItem ("thought", t) = "Thought: " ++ t
    formatItem ("action", a) = "Action: " ++ a
    formatItem ("action_input", i) = "Action Input: " ++ i
    formatItem ("observation", o) = "Observation: " ++ o
    formatItem _ = ""

-- LLM response types
data LLMAction = FinalAnswer String | Action String String | NoAction

-- Parse LLM response
parseLLMResponse :: String -> LLMAction
parseLLMResponse response
    | "Final Answer:" `isInfixOf` response =
        let parts = splitOn "Final Answer:" response
        in case parts of
            [_, answer] -> FinalAnswer (trim $ takeWhile (/= '\n') answer)
            _ -> NoAction
    | "Action:" `isInfixOf` response && "Action Input:" `isInfixOf` response =
        case parseAction response of
            Just (action, input) -> Action action input
            Nothing -> NoAction
    | otherwise = NoAction
  where
    isInfixOf needle haystack = any (isPrefixOf needle) (tails haystack)
    isPrefixOf [] _ = True
    isPrefixOf _ [] = False
    isPrefixOf (x:xs) (y:ys) = x == y && isPrefixOf xs ys
    tails [] = [[]]
    tails xs@(_:xs') = xs : tails xs'
    splitOn delim str = 
        let (prefix, suffix) = breakOn delim str
        in if null suffix then [prefix] else [prefix, drop (length delim) suffix]
    breakOn delim str = 
        case findIndex (isPrefixOf delim) (tails str) of
            Nothing -> (str, "")
            Just i -> splitAt i str
    findIndex p xs = lookup True $ zip (map p xs) [0..]

parseAction :: String -> Maybe (String, String)
parseAction response = do
    let lines' = lines response
    actionLine <- find ("Action:" `isInfixOf`) lines'
    inputLine <- find ("Action Input:" `isInfixOf`) lines'
    let action = trim $ drop (length ("Action:" :: String)) $ dropWhile (/= ':') actionLine
    let input = trim $ drop (length ("Action Input:" :: String)) $ dropWhile (/= ':') inputLine
    return (action, input)
  where
    isInfixOf needle haystack = any (isPrefixOf needle) (tails haystack)
    isPrefixOf [] _ = True
    isPrefixOf _ [] = False
    isPrefixOf (x:xs) (y:ys) = x == y && isPrefixOf xs ys
    tails [] = [[]]
    tails xs@(_:xs') = xs : tails xs'
    find p xs = case filter p xs of
                    [] -> Nothing
                    (x:_) -> Just x

-- Extract thought from response
extractThought :: String -> String
extractThought response
    | (response :: String) =~ ("Thought:\\s*([^\n]+)" :: String) :: Bool =
        let matches = (response :: String) =~ ("Thought:\\s*([^\n]+)" :: String) :: [[String]]
        in case matches of
            [[_, thought]] -> trim thought
            _ -> ""
    | otherwise = ""

-- Trim whitespace
trim :: String -> String
trim = T.unpack . T.strip . T.pack

-- Call LLM
callLLM :: String -> String -> String -> FilePath -> IO String
callLLM modelStr systemPrompt userPrompt logFile = do
    -- Get API configuration
    (apiKey, baseUrl) <- getAPIConfig modelStr
    
    -- Prepare request
    let modelName = getModelName modelStr
        requestBody = ChatRequest
            { chatModel = T.pack modelName
            , messages = 
                [ ChatMessage "system" (T.pack systemPrompt)
                , ChatMessage "user" (T.pack userPrompt)
                ]
            , temperature = 0
            , max_tokens = 2000
            }
    
    -- Make request
    request <- parseRequest $ baseUrl ++ "/chat/completions"
    let request' = setRequestMethod "POST"
                 $ setRequestHeader "Authorization" ["Bearer " <> TE.encodeUtf8 (T.pack apiKey)]
                 $ setRequestHeader "Content-Type" ["application/json"]
                 $ setRequestBodyLBS (encode requestBody)
                 $ request
    
    response <- httpLBS request'
    
    case getResponseStatusCode response of
        200 -> do
            case decode (getResponseBody response) :: Maybe ChatResponse of
                Just chatResp -> case choices chatResp of
                    (choice:_) -> do
                        let contentStr = T.unpack $ content $ message choice
                        logDebug logFile $ "LLM Response: " ++ contentStr
                        return contentStr
                    [] -> error "No choices in response"
                Nothing -> error "Failed to parse response"
        code -> error $ "HTTP " ++ show code ++ ": " ++ BL8.unpack (getResponseBody response)

-- Get API configuration
getAPIConfig :: String -> IO (String, String)
getAPIConfig modelStr = case break (== '/') modelStr of
    ("openai", _) -> do
        apiKey <- lookupEnv "OPENAI_API_KEY"
        case apiKey of
            Just key -> return (key, "https://api.openai.com/v1")
            Nothing -> error "OPENAI_API_KEY not set"
    ("gemini", _) -> do
        apiKey <- lookupEnv "GEMINI_API_KEY"
        case apiKey of
            Just key -> return (key, "https://generativelanguage.googleapis.com/v1beta")
            Nothing -> error "GEMINI_API_KEY not set"
    _ -> error $ "Unsupported model: " ++ modelStr

-- Get model name from model string
getModelName :: String -> String
getModelName modelStr = case break (== '/') modelStr of
    (_, '/':name) -> name
    _ -> modelStr

-- Execute action
executeAction :: String -> String -> String -> FilePath -> IO String
executeAction "find_all_matching_files" input repoPath _ = do
    -- Parse JSON input (simple parsing for this use case)
    let pattern = extractPattern input
        directory = extractDirectory input repoPath
    
    -- Find files
    files <- Main.findFiles directory pattern
    return $ unlines files

executeAction "read_file" input _ logFile = do
    -- Parse JSON input
    let filePath = extractFilePath input
    
    -- Read file
    catch
        (do
            content <- readFile filePath
            -- Limit size
            return $ if length content > 10000
                then take 10000 content ++ "\n[truncated]"
                else content)
        (\e -> return $ "Error reading file: " ++ show (e :: SomeException))

executeAction action _ _ _ = return $ "Error: Unknown action '" ++ action ++ "'"

-- Simple JSON extraction helpers
extractPattern :: String -> String
extractPattern input
    | (input :: String) =~ ("\"pattern\"\\s*:\\s*\"([^\"]+)\"" :: String) :: Bool =
        let [[_, pattern]] = (input :: String) =~ ("\"pattern\"\\s*:\\s*\"([^\"]+)\"" :: String) :: [[String]]
        in pattern
    | otherwise = "*"

extractDirectory :: String -> String -> String
extractDirectory input defaultDir
    | (input :: String) =~ ("\"directory\"\\s*:\\s*\"([^\"]+)\"" :: String) :: Bool =
        let [[_, dir]] = (input :: String) =~ ("\"directory\"\\s*:\\s*\"([^\"]+)\"" :: String) :: [[String]]
        in dir
    | (input :: String) =~ ("\"path\"\\s*:\\s*\"([^\"]+)\"" :: String) :: Bool =
        let [[_, dir]] = (input :: String) =~ ("\"path\"\\s*:\\s*\"([^\"]+)\"" :: String) :: [[String]]
        in dir
    | otherwise = defaultDir

extractFilePath :: String -> String
extractFilePath input
    | (input :: String) =~ ("\"file_path\"\\s*:\\s*\"([^\"]+)\"" :: String) :: Bool =
        let [[_, path]] = (input :: String) =~ ("\"file_path\"\\s*:\\s*\"([^\"]+)\"" :: String) :: [[String]]
        in path
    | otherwise = ""

-- Find files matching pattern
findFiles :: String -> String -> IO [String]
findFiles directory pattern = do
    let findCmd = "find " ++ directory ++ " -type f -name '" ++ pattern ++ "' 2>/dev/null"
    result <- readProcess "sh" ["-c", findCmd] ""
    return $ lines result

-- Extract final answer from memory
extractFinalAnswer :: [(String, String)] -> String
extractFinalAnswer memory = case reverse memory of
    [] -> "No analysis generated"
    ((_, obs):_) -> obs

-- Save metadata
saveMetadata :: Args -> String -> String -> String -> IO ()
saveMetadata Args{..} result outputFile metadataFile = do
    timestamp <- formatTime defaultTimeLocale "%Y-%m-%dT%H:%M:%S" <$> getCurrentTime
    let metadata = Metadata
            { metaRepo = T.pack repo
            , metaPromptFile = T.pack promptFile
            , metaModel = T.pack model
            , metaTimestamp = T.pack timestamp
            , wordCount = length $ words result
            , charCount = length result
            }
    BL.writeFile metadataFile $ encodePretty metadata